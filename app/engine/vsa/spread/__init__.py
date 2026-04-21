"""Spread Module."""
from app.engine.vsa.spread.analysis import SpreadAnalysis
from app.engine.vsa.spread.narrow_spread import NarrowSpreadDetector
from app.engine.vsa.spread.wide_spread import WideSpreadDetector

__all__ = ["SpreadAnalysis", "NarrowSpreadDetector", "WideSpreadDetector"]