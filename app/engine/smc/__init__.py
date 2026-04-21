"""SMC Module - Smart Money Concept (Profondeur équivalente à ICT)."""
from app.engine.smc.analyzer import SMCAnalyzer
from app.engine.smc.confidence import SMCConfidenceCalculator
from app.engine.smc.signal_builder import SMCSignalBuilder
from app.engine.smc.models import (
    SMCSignal, WyckoffPhase, SpringUpthrust, SupplyDemandZone, MarketMakerModel,
)

# Sous-modules Wyckoff
from app.engine.smc.wyckoff import WyckoffPhases, WyckoffSchematics, VolumeConfirmation

# Sous-modules Volume
from app.engine.smc.volume import VolumeAnalysis, VolumeClimaxDetector, VolumeDivergence

# Sous-modules Patterns
from app.engine.smc.patterns import (
    SpringDetector, UpthrustDetector, TerminalShakeoutDetector, AbsorptionDetector
)

# Sous-modules Order Flow
from app.engine.smc.order_flow import DeltaAnalyzer, FootprintAnalyzer, POCAnalyzer

# Sous-modules Market Maker
from app.engine.smc.market_maker import MarketMakerModels, StopHuntDetector, LiquidityGrabDetector

# Sous-modules Liquidité SMC
from app.engine.smc.liquidity_smc import LiquidityPoolsSMC, InducementDetectorSMC, StopHuntDetectorSMC

# Sous-modules Supply/Demand
from app.engine.smc.supply_demand import SupplyDemandZones, FreshZones, ZoneStrength

# Alias pour éviter conflits avec ICT
WyckoffAnalyzer = WyckoffPhases
VolumeAnalyzer = VolumeAnalysis
SpringUpthrustDetector = SpringDetector
OrderFlowAnalyzer = DeltaAnalyzer
MarketMakerAnalyzer = MarketMakerModels
LiquidityAnalyzerSMC = LiquidityPoolsSMC
SupplyDemandAnalyzer = SupplyDemandZones

__all__ = [
    # Core
    "SMCAnalyzer", "SMCConfidenceCalculator", "SMCSignalBuilder",
    "SMCSignal", "WyckoffPhase", "SpringUpthrust", "SupplyDemandZone", "MarketMakerModel",
    
    # Wyckoff
    "WyckoffAnalyzer", "WyckoffPhases", "WyckoffSchematics", "VolumeConfirmation",
    
    # Volume
    "VolumeAnalyzer", "VolumeAnalysis", "VolumeClimaxDetector", "VolumeDivergence",
    
    # Patterns
    "SpringUpthrustDetector", "SpringDetector", "UpthrustDetector", 
    "TerminalShakeoutDetector", "AbsorptionDetector",
    
    # Order Flow
    "OrderFlowAnalyzer", "DeltaAnalyzer", "FootprintAnalyzer", "POCAnalyzer",
    
    # Market Maker
    "MarketMakerAnalyzer", "MarketMakerModels", "StopHuntDetector", "LiquidityGrabDetector",
    
    # Liquidité
    "LiquidityAnalyzerSMC", "LiquidityPoolsSMC", "InducementDetectorSMC", "StopHuntDetectorSMC",
    
    # Supply/Demand
    "SupplyDemandAnalyzer", "SupplyDemandZones", "FreshZones", "ZoneStrength",
]