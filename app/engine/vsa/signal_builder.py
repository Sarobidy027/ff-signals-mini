"""Constructeur de signaux VSA."""
from datetime import datetime
import uuid

from app.engine.vsa.models import VSASignal, SpreadAnalysis, VolumeClimax, EffortResult


class VSASignalBuilder:
    """Construit un signal VSA à partir des composants."""
    
    def build(
        self, instrument: str, timeframe: str, confidence: float,
        spread_analysis: SpreadAnalysis = None, climax: VolumeClimax = None,
        stopping: dict = None, effort: EffortResult = None,
        entry: float = 0.0, sl: float = 0.0, tp: float = 0.0,
        direction: str = "BUY",
    ) -> VSASignal:
        
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr = round(reward / risk, 2) if risk > 0 else 1.0
        
        validation_score = confidence
        if spread_analysis:
            validation_score = min(validation_score + 5, 100)
        if climax:
            validation_score = min(validation_score + 5, 100)
        if stopping:
            validation_score = min(validation_score + 5, 100)
        if effort:
            validation_score = min(validation_score + 5, 100)
        
        return VSASignal(
            id=str(uuid.uuid4()), instrument=instrument, direction=direction,
            confidence=confidence, spread_analysis=spread_analysis,
            volume_climax=climax, stopping_volume=stopping,
            effort_result=effort, entry_price=entry,
            stop_loss=sl, take_profit=tp, risk_reward_ratio=rr,
            timeframe=timeframe, created_at=datetime.utcnow(),
            validation_score=validation_score,
        )