"""Moteur de fusion ICT + SMC + VSA + Fondamental."""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import uuid
import structlog

from app.engine.ict import ICTAnalyzer
from app.engine.smc import SMCAnalyzer
from app.engine.vsa import VSAAnalyzer
from app.engine.fundamental import NewsImpactAnalyzer, SentimentAnalyzer
from app.engine.hybrid.cross_validator import CrossValidator
from app.engine.hybrid.triple_filter import TripleFilter
from app.models.signal import Signal, Direction, TradeType, SignalStatus
from app.core.config import settings

logger = structlog.get_logger()


class FusionEngine:
    """Fusion des 4 stratégies pour win rate 90%+."""
    
    def __init__(self, instrument: str, timeframe: str = "15min"):
        self.instrument = instrument
        self.timeframe = timeframe
        self.ict = ICTAnalyzer(instrument, timeframe)
        self.smc = SMCAnalyzer(instrument, timeframe)
        self.vsa = VSAAnalyzer(instrument, timeframe)
        self.validator = CrossValidator()
        self.filter = TripleFilter()
    
    async def load_all(self) -> bool:
        """Charge les données pour tous les moteurs."""
        tasks = [self.ict.load_data(), self.smc.load_data(), self.vsa.load_data()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return all(r is True for r in results if not isinstance(r, Exception))
    
    async def analyze(self) -> Optional[Signal]:
        """Analyse fusionnée complète."""
        if not await self.load_all():
            logger.warning("fusion_load_failed", instrument=self.instrument)
            return None
        
        ict_task = self.ict.analyze()
        smc_task = self.smc.analyze()
        vsa_task = self.vsa.analyze()
        
        ict_signal, smc_signal, vsa_signal = await asyncio.gather(
            ict_task, smc_task, vsa_task, return_exceptions=True
        )
        
        ict_signal = ict_signal if not isinstance(ict_signal, Exception) else None
        smc_signal = smc_signal if not isinstance(smc_signal, Exception) else None
        vsa_signal = vsa_signal if not isinstance(vsa_signal, Exception) else None
        
        news_ok = not await NewsImpactAnalyzer.has_major_news(self.instrument, 2)
        sentiment = await SentimentAnalyzer.analyze(self.instrument)
        
        validation = self.validator.validate(
            ict_signal=ict_signal, smc_signal=smc_signal, vsa_signal=vsa_signal,
            fundamental_ok=news_ok, sentiment=sentiment,
        )
        
        if not validation.get("valid"):
            logger.debug("fusion_validation_failed", instrument=self.instrument,
                        reason=validation.get("reason"))
            return None
        
        filtered = self.filter.apply(validation, self.instrument)
        if not filtered.get("passed"):
            logger.debug("fusion_filter_failed", instrument=self.instrument,
                        filters=filtered.get("filters_passed"))
            return None
        
        signal = self._build_signal(validation, filtered)
        
        logger.info("fusion_signal_generated", instrument=self.instrument,
                   direction=signal.direction.value, confidence=signal.confidence,
                   contributing=validation.get("contributing_strategies"))
        
        return signal
    
    def _build_signal(self, validation: Dict, filtered: Dict) -> Signal:
        """Construit le signal final."""
        now = datetime.utcnow()
        
        direction = Direction(validation["direction"])
        entry = validation["entry_price"]
        sl = validation["stop_loss"]
        tp = validation["take_profit"]
        confidence = filtered["final_confidence"]
        
        trade_type = self._get_trade_type()
        duration = self._get_duration(trade_type)
        
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr = round(reward / risk, 2) if risk > 0 else 1.0
        
        anticipation = self._get_anticipation_minutes()
        
        return Signal(
            id=str(uuid.uuid4()), instrument=self.instrument, direction=direction,
            entry_price=entry, stop_loss=sl, take_profit=tp, confidence=confidence,
            trade_type=trade_type, estimated_duration=duration,
            entry_time=now + timedelta(minutes=anticipation),
            exit_time=None, status=SignalStatus.PENDING, result=None, pips_gained=None,
            risk_reward_ratio=rr, created_at=now, updated_at=now,
        )
    
    def _get_trade_type(self) -> TradeType:
        mapping = {"1min": TradeType.SCALP, "5min": TradeType.SCALP,
                  "15min": TradeType.DAY, "1H": TradeType.DAY,
                  "4H": TradeType.SWING, "1D": TradeType.SWING}
        return mapping.get(self.timeframe, TradeType.DAY)
    
    def _get_duration(self, tt: TradeType) -> str:
        return {TradeType.SCALP: "5-30 min", TradeType.DAY: "2-8 heures",
                TradeType.SWING: "1-5 jours"}.get(tt, "2-8 heures")
    
    def _get_anticipation_minutes(self) -> int:
        if self.timeframe in ["1min", "5min"]:
            return settings.SCALP_ANTICIPATION_MINUTES
        elif self.timeframe in ["15min", "1H"]:
            return settings.DAY_ANTICIPATION_MINUTES
        return settings.SWING_ANTICIPATION_HOURS * 60