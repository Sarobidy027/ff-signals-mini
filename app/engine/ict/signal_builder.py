"""Constructeur de signaux ICT."""
from datetime import datetime
import uuid

from app.models.signal import Signal, SignalCreate, Direction, TradeType, SignalStatus
from app.models.signal_context import SignalContext
from app.utils.validation_utils import validate_signal
from app.core.config import settings


class SignalBuilder:
    """Construit un Signal à partir d'un SignalContext."""
    
    @staticmethod
    def from_context(ctx: SignalContext) -> SignalCreate:
        return SignalCreate(
            instrument=ctx.instrument,
            direction=Direction(ctx.direction),
            entry_price=ctx.entry_price,
            stop_loss=ctx.stop_loss,
            take_profit=ctx.take_profit,
            confidence=ctx.confidence,
            trade_type=TradeType(ctx.trade_type),
            entry_time=ctx.entry_time,
        )
    
    @staticmethod
    def build(signal_create: SignalCreate) -> Signal:
        durations = {"SCALP": "5-30 min", "DAY": "2-8 heures", "SWING": "1-5 jours"}
        risk = abs(signal_create.entry_price - signal_create.stop_loss)
        reward = abs(signal_create.take_profit - signal_create.entry_price)
        rr = round(reward / risk, 2) if risk > 0 else 1.0
        now = datetime.utcnow()
        
        signal = Signal(
            id=str(uuid.uuid4()),
            instrument=signal_create.instrument,
            direction=signal_create.direction,
            entry_price=signal_create.entry_price,
            stop_loss=signal_create.stop_loss,
            take_profit=signal_create.take_profit,
            confidence=signal_create.confidence,
            trade_type=signal_create.trade_type,
            estimated_duration=durations.get(signal_create.trade_type.value, "2-8 heures"),
            entry_time=signal_create.entry_time,
            exit_time=None,
            status=SignalStatus.PENDING,
            result=None,
            pips_gained=None,
            risk_reward_ratio=rr,
            created_at=now,
            updated_at=now,
        )
        
        errors = validate_signal(signal)
        if errors:
            raise ValueError(f"Invalid signal: {', '.join(errors)}")
        
        return signal