"""Constructeur de signaux SMC."""
from datetime import datetime
import uuid

from app.engine.smc.models import SMCSignal, WyckoffPhase, SpringUpthrust, SupplyDemandZone, MarketMakerModel


class SMCSignalBuilder:
    """Construit un signal SMC à partir des composants."""
    
    def build(
        self, instrument: str, timeframe: str, confidence: float,
        wyckoff_phase=None, spring_upthrust=None, sd_zones=None,
        mmm=None, current_price: float = 0.0,
    ) -> SMCSignal:
        
        direction = self._determine_direction(wyckoff_phase, spring_upthrust, mmm)
        entry, sl, tp = self._calculate_levels(direction, spring_upthrust, mmm, current_price)
        
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        rr = round(reward / risk, 2) if risk > 0 else 1.0
        
        relevant_zone = None
        if sd_zones:
            zones = [z for z in sd_zones if z.zone_type == ("DEMAND" if direction == "BUY" else "SUPPLY")]
            if zones:
                relevant_zone = max(zones, key=lambda z: z.strength)
        
        # Validation score basé sur les composants présents
        validation_score = confidence
        if wyckoff_phase:
            validation_score = min(validation_score + 5, 100)
        if spring_upthrust:
            validation_score = min(validation_score + 5, 100)
        if mmm:
            validation_score = min(validation_score + 5, 100)
        if relevant_zone:
            validation_score = min(validation_score + 5, 100)
        
        return SMCSignal(
            id=str(uuid.uuid4()), instrument=instrument, direction=direction,
            confidence=confidence, wyckoff_phase=wyckoff_phase,
            spring_upthrust=spring_upthrust, supply_demand_zone=relevant_zone,
            market_maker_model=mmm, entry_price=entry, stop_loss=sl, take_profit=tp,
            risk_reward_ratio=rr, timeframe=timeframe, created_at=datetime.utcnow(),
            validation_score=validation_score,
        )
    
    def _determine_direction(self, wyckoff, spring, mmm) -> str:
        if spring:
            return spring.direction
        if mmm:
            return "BUY" if mmm.direction == "BULLISH" else "SELL"
        if wyckoff:
            if wyckoff.phase_type.value.startswith("ACCUMULATION"):
                return "BUY"
            elif wyckoff.phase_type.value.startswith("DISTRIBUTION"):
                return "SELL"
        return "BUY"
    
    def _calculate_levels(self, direction, spring, mmm, price):
        if spring:
            return spring.entry_price, spring.stop_loss, spring.take_profit
        if mmm:
            entry = sum(mmm.entry_zone) / 2
            return entry, mmm.stop_loss, mmm.targets[0] if mmm.targets else entry * 1.02
        atr = price * 0.002
        if direction == "BUY":
            return price, price - atr * 1.5, price + atr * 2.5
        return price, price + atr * 1.5, price - atr * 2.5