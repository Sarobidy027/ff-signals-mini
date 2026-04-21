"""Patterns Module."""
from app.engine.smc.patterns.spring import SpringDetector
from app.engine.smc.patterns.upthrust import UpthrustDetector
from app.engine.smc.patterns.terminal_shakeout import TerminalShakeoutDetector
from app.engine.smc.patterns.absorption import AbsorptionDetector

__all__ = ["SpringDetector", "UpthrustDetector", "TerminalShakeoutDetector", "AbsorptionDetector"]