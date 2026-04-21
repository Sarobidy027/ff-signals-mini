"""
Analyseur ICT principal.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import numpy as np
import uuid
import structlog

from app.data.market_providers import MarketProviderFactory, CandleData
from app.data.instruments import get_current_price, get_spread
from app.data.news import has_major_news, get_sentiment
from app.utils.numpy_utils import calculate_atr
from app.utils.validation_utils import validate_rr_ratio
from app.models.signal_context import SignalContext
from app.models.order_block import OrderBlock
from app.engine.ict.market_structure import SwingPoints, BOSChoCH, MSS
from app.engine.ict.order_blocks import OrderBlockDetector, BaseOrderBlock
from app.engine.ict.imbalances import FVGDetector
from app.engine.ict.liquidity import LiquidityPools
from app.engine.ict.time_price import Killzone, PremiumDiscount
from app.engine.ict.confluence import MultiTFAlignment
from app.engine.ict.confidence import ConfidenceCalculator
from app.core.config import settings

logger = structlog.get_logger()


def _candles_to_arrays(candles: List[CandleData]) -> Dict[str, np.ndarray]:
    """Convertit les bougies en arrays numpy."""
    return {
        'open': np.array([c.open for c in candles]),
        'high': np.array([c.high for c in candles]),
        'low': np.array([c.low for c in candles]),
        'close': np.array([c.close for c in candles]),
        'volume': np.array([c.volume for c in candles]),
    }


class ICTAnalyzer:
    """Analyseur ICT complet."""
    
    def __init__(self, instrument: str, timeframe: str = "15min"):
        self.instrument = instrument
        self.timeframe = timeframe
        self.candles: List[CandleData] = []
        self._arrays: Dict[str, np.ndarray] = {}
        self._loaded = False
    
    async def load_data(self) -> bool:
        """Charge les données de marché."""
        try:
            self.candles = await MarketProviderFactory.get_candles(
                self.instrument, self.timeframe, count=200
            )
            self._loaded = len(self.candles) >= 50
            if self._loaded:
                self._arrays = _candles_to_arrays(self.candles)
                logger.debug("ict_data_loaded", instrument=self.instrument, 
                           timeframe=self.timeframe, candles=len(self.candles))
            return self._loaded
        except Exception as e:
            logger.error("ict_load_failed", instrument=self.instrument, error=str(e))
            return False
    
    async def analyze(self) -> Optional[SignalContext]:
        """Analyse ICT complète."""
        if not self._loaded and not await self.load_data():
            return None
        if len(self.candles) < 50:
            logger.debug("ict_insufficient_data", instrument=self.instrument)
            return None
        
        current_price = await get_current_price(self.instrument)
        if current_price <= 0:
            current_price = self.candles[-1].close
        
        spread = get_spread(self.instrument)
        
        # Structure de marché
        swings = SwingPoints.detect(self.candles)
        bos = BOSChoCH.detect_bos(self.candles, swings, "BULLISH") + \
              BOSChoCH.detect_bos(self.candles, swings, "BEARISH")
        choch = BOSChoCH.detect_choch(self.candles, swings)
        mss = MSS.detect(self.candles, swings)
        
        # Order Blocks et FVGs
        order_blocks = OrderBlockDetector.find_all(self.candles, self.instrument, self.timeframe)
        active_obs = [ob for ob in order_blocks if ob.is_active and not ob.mitigated]
        fvgs = FVGDetector.find(self.candles, self.instrument, self.timeframe)
        unfilled_fvgs = FVGDetector.find_unfilled_fvgs(fvgs, self.candles)
        
        # Liquidité
        liquidity_data = LiquidityPools.find(self.candles, swings)
        
        # Confluence
        htf_bias = await MultiTFAlignment.get_bias(self.instrument)
        in_killzone = Killzone.is_active()
        
        # Fondamental
        fundamental_ok = not await has_major_news(self.instrument, 2)
        sentiment = await get_sentiment(self.instrument)
        
        # Direction
        direction = self._determine_direction(
            swings, bos, choch, mss, order_blocks, htf_bias, current_price, sentiment
        )
        if not direction:
            return None
        
        # Niveaux
        nearest_ob = BaseOrderBlock.find_nearest_ob(
            active_obs, current_price, "BULLISH" if direction == "BUY" else "BEARISH"
        )
        liquidity_target = LiquidityPools.find_nearest_liquidity(
            liquidity_data["pools"], current_price, "ABOVE" if direction == "BUY" else "BELOW"
        )
        
        sl = self._calculate_sl(current_price, nearest_ob, direction, spread)
        tp = self._calculate_tp(current_price, liquidity_target, direction)
        if not sl or not tp:
            return None
        
        if not validate_rr_ratio(current_price, sl, tp, direction):
            logger.debug("ict_rr_invalid", instrument=self.instrument)
            return None
        
        rr = self._calculate_rr(current_price, sl, tp)
        
        # Confiance
        confidence = ConfidenceCalculator.compute(
            htf_bias=htf_bias, mss=mss, order_blocks=order_blocks, fvgs=fvgs,
            liquidity_pools=liquidity_data["pools"], in_killzone=in_killzone,
            fundamental_ok=fundamental_ok,
        )
        
        if direction == "BUY" and sentiment > 0:
            confidence = min(confidence + 5, 100)
        elif direction == "SELL" and sentiment < 0:
            confidence = min(confidence + 5, 100)
        
        if confidence < 75:
            logger.debug("ict_confidence_low", instrument=self.instrument, confidence=confidence)
            return None
        
        # Type de trade et anticipation
        trade_type = self._get_trade_type()
        entry_time = self._get_entry_time()
        anticipation = self._get_anticipation_minutes()
        
        logger.info("ict_signal_generated", instrument=self.instrument, 
                   direction=direction, confidence=confidence, trade_type=trade_type)
        
        return SignalContext(
            instrument=self.instrument, direction=direction,
            entry_price=current_price, stop_loss=sl, take_profit=tp,
            confidence=confidence, trade_type=trade_type,
            entry_time=entry_time, risk_reward_ratio=rr,
            active_order_blocks=active_obs[:3], active_fvgs=unfilled_fvgs[:3],
            nearest_liquidity=liquidity_target["price"] if liquidity_target else None,
            htf_bias=htf_bias["direction"], in_killzone=in_killzone,
            fundamental_ok=fundamental_ok,
            anticipation_minutes=anticipation,
            signal_source="ICT",
        )
    
    def _determine_direction(self, swings, bos, choch, mss, obs, htf_bias, price, sentiment) -> Optional[str]:
        if htf_bias["direction"] == "BULLISH" and htf_bias["strength"] > 0.6:
            if any(ob.direction == "BULLISH" and ob.low_price < price for ob in obs):
                return "BUY"
        if htf_bias["direction"] == "BEARISH" and htf_bias["strength"] > 0.6:
            if any(ob.direction == "BEARISH" and ob.high_price > price for ob in obs):
                return "SELL"
        if choch:
            return "BUY" if choch["direction"] == "BULLISH" else "SELL"
        if mss:
            return "BUY" if mss["direction"] == "BULLISH_TRAP" else "SELL"
        if bos:
            return "BUY" if bos[-1]["direction"] == "BULLISH" else "SELL"
        if sentiment > 0.5:
            return "BUY"
        if sentiment < -0.5:
            return "SELL"
        return None
    
    def _calculate_sl(self, price: float, ob: Optional[OrderBlock], direction: str, spread: float) -> float:
        if ob:
            return ob.low_price * (1 - spread) if direction == "BUY" else ob.high_price * (1 + spread)
        atr = self._get_atr()
        return price - atr * 1.5 if direction == "BUY" else price + atr * 1.5
    
    def _calculate_tp(self, price: float, target: Optional[Dict], direction: str) -> float:
        if target:
            return target["price"]
        atr = self._get_atr()
        return price + atr * 2 if direction == "BUY" else price - atr * 2
    
    def _get_atr(self) -> float:
        if not self._arrays:
            return 0.001
        atr = calculate_atr(self._arrays['high'], self._arrays['low'], self._arrays['close'], 14)
        return float(atr[-1]) if not np.isnan(atr[-1]) else 0.001
    
    def _calculate_rr(self, entry: float, sl: float, tp: float) -> float:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        return round(reward / risk, 2) if risk > 0 else 0
    
    def _get_trade_type(self) -> str:
        mapping = {"1min": "SCALP", "5min": "SCALP", "15min": "DAY", "1H": "DAY", "4H": "SWING", "1D": "SWING"}
        return mapping.get(self.timeframe, "DAY")
    
    def _get_anticipation_minutes(self) -> int:
        if self.timeframe in ["1min", "5min"]:
            return settings.SCALP_ANTICIPATION_MINUTES
        elif self.timeframe in ["15min", "1H"]:
            return settings.DAY_ANTICIPATION_MINUTES
        else:
            return settings.SWING_ANTICIPATION_HOURS * 60
    
    def _get_entry_time(self) -> datetime:
        now = datetime.utcnow()
        anticipation = self._get_anticipation_minutes()
        
        if Killzone.is_active():
            return now + timedelta(minutes=anticipation)
        else:
            next_kz = Killzone.get_next_killzone()
            kz_start = datetime.combine(now.date(), next_kz["start"])
            if kz_start <= now:
                kz_start = datetime.combine(now.date() + timedelta(days=1), next_kz["start"])
            return kz_start + timedelta(minutes=anticipation)