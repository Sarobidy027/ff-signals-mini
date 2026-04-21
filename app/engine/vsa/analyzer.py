"""Analyseur VSA principal - Utilise tous les sous-modules."""
from typing import Optional, List
from datetime import datetime
import uuid
import structlog

from app.data.market_providers import MarketProviderFactory, CandleData
from app.data.instruments import get_current_price, get_spread
from app.data.news import has_major_news
from app.utils.validation_utils import validate_rr_ratio
from app.engine.vsa.models import VSASignal
from app.engine.vsa.spread import SpreadAnalyzer, NarrowSpreadDetector, WideSpreadDetector
from app.engine.vsa.volume import RelativeVolumeAnalyzer, StoppingVolumeDetector, ClimaxDetector
from app.engine.vsa.bars import UpthrustBarDetector, ReverseUpthrustDetector, NoDemandDetector, NoSupplyDetector
from app.engine.vsa.effort_result import WyckoffLawAnalyzer, AbsorptionAnalyzer
from app.engine.vsa.confirmation import TrendConfirmation, ReversalSignals
from app.engine.vsa.confidence import VSAConfidenceCalculator
from app.engine.vsa.signal_builder import VSASignalBuilder
from app.core.config import settings

logger = structlog.get_logger()


class VSAAnalyzer:
    """Analyseur Volume Spread Analysis complet - Utilise tous les sous-modules."""
    
    def __init__(self, instrument: str, timeframe: str = "15min"):
        self.instrument = instrument
        self.timeframe = timeframe
        self.candles: List[CandleData] = []
        self._loaded = False
        
        # Sous-modules
        self.spread_analyzer = None
        self.narrow_spread = None
        self.wide_spread = None
        self.volume_analyzer = None
        self.stopping_volume = None
        self.climax_detector = None
        self.upthrust_detector = None
        self.reverse_upthrust = None
        self.no_demand = None
        self.no_supply = None
        self.wyckoff_law = None
        self.absorption = None
        self.trend_confirmation = None
        self.reversal_signals = None
    
    def _init_modules(self):
        """Initialise tous les sous-modules."""
        self.spread_analyzer = SpreadAnalyzer(self.candles)
        self.narrow_spread = NarrowSpreadDetector(self.candles)
        self.wide_spread = WideSpreadDetector(self.candles)
        self.volume_analyzer = RelativeVolumeAnalyzer(self.candles)
        self.stopping_volume = StoppingVolumeDetector(self.candles)
        self.climax_detector = ClimaxDetector(self.candles)
        self.wyckoff_law = WyckoffLawAnalyzer(self.candles)
    
    async def load_data(self) -> bool:
        """Charge les données de marché."""
        try:
            self.candles = await MarketProviderFactory.get_candles(
                self.instrument, self.timeframe, count=200
            )
            self._loaded = len(self.candles) >= 50
            if self._loaded:
                self._init_modules()
                logger.debug("vsa_data_loaded", instrument=self.instrument, candles=len(self.candles))
            return self._loaded
        except Exception as e:
            logger.error("vsa_load_failed", instrument=self.instrument, error=str(e))
            return False
    
    async def analyze(self) -> Optional[VSASignal]:
        """Analyse VSA complète utilisant tous les sous-modules."""
        if not self._loaded and not await self.load_data():
            return None
        if len(self.candles) < 50:
            return None
        
        current_price = await get_current_price(self.instrument)
        if current_price <= 0:
            current_price = self.candles[-1].close
        
        spread = get_spread(self.instrument)
        
        # 1. Spread Analysis
        spread_result = self.spread_analyzer.analyze()
        narrows = self.narrow_spread.detect()
        wides = self.wide_spread.detect()
        
        # 2. Volume Analysis
        volume_result = self.volume_analyzer.analyze()
        stopping = self.stopping_volume.detect()
        climax = self.climax_detector.detect()
        
        # 3. Bar Analysis
        upthrusts = UpthrustBarDetector.detect(self.candles)
        springs = ReverseUpthrustDetector.detect(self.candles)
        no_demands = NoDemandDetector.detect(self.candles)
        no_supplies = NoSupplyDetector.detect(self.candles)
        
        # 4. Effort vs Résultat
        effort_result = self.wyckoff_law.analyze()
        absorptions = AbsorptionAnalyzer.detect(self.candles)
        
        # 5. Confirmation
        trend_confirm = TrendConfirmation.confirm(self.candles)
        reversal = ReversalSignals.detect(self.candles)
        
        # 6. Bar signal le plus fort
        bar_signal = None
        if upthrusts:
            bar_signal = upthrusts[0]
        elif springs:
            bar_signal = springs[0]
        elif no_demands:
            bar_signal = no_demands[0]
        elif no_supplies:
            bar_signal = no_supplies[0]
        
        # 7. Données pour la confiance
        confidence_data = {
            "spread_result": spread_result,
            "narrows": narrows,
            "wides": wides,
            "volume_result": volume_result,
            "stopping": stopping,
            "climax": climax,
            "bar_signal": bar_signal,
            "effort_result": effort_result,
            "absorptions": absorptions,
            "trend_confirm": trend_confirm,
            "reversal": reversal,
        }
        
        confidence = VSAConfidenceCalculator.compute(confidence_data)
        
        if confidence < 70:
            logger.debug("vsa_confidence_low", instrument=self.instrument, confidence=confidence)
            return None
        
        # 8. Fondamental
        fundamental_ok = not await has_major_news(self.instrument, 2)
        if not fundamental_ok:
            confidence = max(confidence - 10, 0)
        
        # 9. Direction
        direction = self._determine_direction(bar_signal, stopping, climax, trend_confirm, reversal)
        if not direction:
            return None
        
        # 10. Niveaux
        entry, sl, tp = self._calculate_levels(direction, current_price, spread, bar_signal, stopping, climax)
        
        if not validate_rr_ratio(entry, sl, tp, direction):
            return None
        
        rr = self._calc_rr(entry, sl, tp)
        
        signal = VSASignal(
            id=str(uuid.uuid4()), instrument=self.instrument,
            direction="BUY" if direction == "BULLISH" else "SELL",
            confidence=confidence, spread_analysis=spread_result,
            volume_climax=climax, stopping_volume=stopping,
            effort_result=effort_result, entry_price=entry,
            stop_loss=sl, take_profit=tp, risk_reward_ratio=rr,
            timeframe=self.timeframe, created_at=datetime.utcnow(),
            validation_score=confidence,
        )
        
        logger.info("vsa_signal_generated", instrument=self.instrument,
                   direction=signal.direction, confidence=confidence,
                   components={
                       "spread": spread_result.spread_type,
                       "climax": climax.climax_type if climax else None,
                       "stopping": stopping is not None,
                       "effort": effort_result.signal if effort_result else None,
                   })
        
        return signal
    
    def _determine_direction(self, bar, stopping, climax, trend, reversal) -> Optional[str]:
        if bar:
            return bar["direction"]
        if stopping:
            return stopping["direction"]
        if climax and climax.confidence >= 75:
            return climax.expected_reversal
        if reversal:
            return reversal["direction"]
        if trend.get("confirmed"):
            return trend["direction"]
        return None
    
    def _calculate_levels(self, direction: str, price: float, spread: float,
                         bar: dict, stopping: dict, climax) -> tuple:
        if bar:
            return bar.get("entry", price), bar.get("stop", price * 0.998), bar.get("target", price * 1.004)
        if stopping:
            return stopping.get("entry", price), stopping.get("stop", price * 0.998), stopping.get("target", price * 1.004)
        
        atr = price * 0.002
        if direction == "BULLISH":
            return price + spread, price - atr * 1.5, price + atr * 2.5
        return price - spread, price + atr * 1.5, price - atr * 2.5
    
    def _calc_rr(self, entry: float, sl: float, tp: float) -> float:
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        return round(reward / risk, 2) if risk > 0 else 1.0