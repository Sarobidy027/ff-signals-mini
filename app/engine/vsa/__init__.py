"""VSA Module - Volume Spread Analysis (Profondeur équivalente à ICT)."""
from app.engine.vsa.analyzer import VSAAnalyzer
from app.engine.vsa.confidence import VSAConfidenceCalculator
from app.engine.vsa.signal_builder import VSASignalBuilder
from app.engine.vsa.models import VSASignal, SpreadAnalysis, VolumeClimax, EffortResult

# Sous-modules Spread
from app.engine.vsa.spread import SpreadAnalyzer, NarrowSpreadDetector, WideSpreadDetector

# Sous-modules Volume
from app.engine.vsa.volume import RelativeVolumeAnalyzer, StoppingVolumeDetector, ClimaxDetector

# Sous-modules Bars
from app.engine.vsa.bars import (
    UpthrustBarDetector, ReverseUpthrustDetector, NoDemandDetector, NoSupplyDetector
)

# Sous-modules Effort/Résultat
from app.engine.vsa.effort_result import WyckoffLawAnalyzer, AbsorptionAnalyzer

# Sous-modules Confirmation
from app.engine.vsa.confirmation import TrendConfirmation, ReversalSignals

# Alias pour uniformité
VolumeAnalyzerVSA = RelativeVolumeAnalyzer
BarAnalyzer = UpthrustBarDetector
EffortResultAnalyzer = WyckoffLawAnalyzer
ConfirmationAnalyzer = TrendConfirmation

__all__ = [
    # Core
    "VSAAnalyzer", "VSAConfidenceCalculator", "VSASignalBuilder",
    "VSASignal", "SpreadAnalysis", "VolumeClimax", "EffortResult",
    
    # Spread
    "SpreadAnalyzer", "NarrowSpreadDetector", "WideSpreadDetector",
    
    # Volume
    "VolumeAnalyzerVSA", "RelativeVolumeAnalyzer", "StoppingVolumeDetector", "ClimaxDetector",
    
    # Bars
    "BarAnalyzer", "UpthrustBarDetector", "ReverseUpthrustDetector",
    "NoDemandDetector", "NoSupplyDetector",
    
    # Effort/Résultat
    "EffortResultAnalyzer", "WyckoffLawAnalyzer", "AbsorptionAnalyzer",
    
    # Confirmation
    "ConfirmationAnalyzer", "TrendConfirmation", "ReversalSignals",
]