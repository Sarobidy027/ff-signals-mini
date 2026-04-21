"""
Moteur d'analyse et de génération de signaux.
FF SIGNALS MINI - 4 stratégies complètes avec profondeur équivalente.
"""
# ICT - Complet
from app.engine.ict import (
    ICTAnalyzer, ConfidenceCalculator as ICTConfidence, SignalBuilder as ICTSignalBuilder,
    SwingPoints, BOSChoCH, MSS,
    OrderBlockDetector, BaseOrderBlock, BreakerBlock, MitigationBlock, RejectionBlock, VacuumBlock,
    FVGDetector, ImpliedFVGDetector, VolumeImbalanceDetector, GapDetector,
    LiquidityPools, InducementDetector as ICTInducement, StopHuntDetector as ICTStopHunt,
    Killzone, PremiumDiscount, FibonacciTools,
    MultiTFAlignment, SmartMoneyReversal, TurtleSoup,
)

# SMC - Complet (même profondeur)
from app.engine.smc import (
    SMCAnalyzer, SMCConfidenceCalculator, SMCSignalBuilder,
    SMCSignal, WyckoffPhase, SpringUpthrust, SupplyDemandZone, MarketMakerModel,
    WyckoffAnalyzer, VolumeAnalyzer as SMCVolumeAnalyzer, SpringUpthrustDetector,
    OrderFlowAnalyzer, MarketMakerAnalyzer, LiquidityAnalyzerSMC, SupplyDemandAnalyzer,
)

# VSA - Complet (même profondeur)
from app.engine.vsa import (
    VSAAnalyzer, VSAConfidenceCalculator, VSASignalBuilder,
    VSASignal, SpreadAnalysis, VolumeClimax, EffortResult,
    SpreadAnalyzer, VolumeAnalyzerVSA, BarAnalyzer,
    EffortResultAnalyzer, ConfirmationAnalyzer,
)

# Hybrid - Fusion
from app.engine.hybrid import (
    FusionEngine, CrossValidator, TripleFilter,
)

# Fundamental
from app.engine.fundamental import (
    NewsImpactAnalyzer, SentimentAnalyzer, EconomicCalendar,
)

# Signal Generation
from app.engine.signal_generator import SignalGenerator
from app.engine.signal_scheduler import SignalScheduler, scheduler

__all__ = [
    # ICT
    "ICTAnalyzer", "ICTConfidence", "ICTSignalBuilder",
    "SwingPoints", "BOSChoCH", "MSS",
    "OrderBlockDetector", "BaseOrderBlock", "BreakerBlock", "MitigationBlock",
    "RejectionBlock", "VacuumBlock",
    "FVGDetector", "ImpliedFVGDetector", "VolumeImbalanceDetector", "GapDetector",
    "LiquidityPools", "ICTInducement", "ICTStopHunt",
    "Killzone", "PremiumDiscount", "FibonacciTools",
    "MultiTFAlignment", "SmartMoneyReversal", "TurtleSoup",
    
    # SMC
    "SMCAnalyzer", "SMCConfidenceCalculator", "SMCSignalBuilder",
    "SMCSignal", "WyckoffPhase", "SpringUpthrust", "SupplyDemandZone", "MarketMakerModel",
    "WyckoffAnalyzer", "SMCVolumeAnalyzer", "SpringUpthrustDetector",
    "OrderFlowAnalyzer", "MarketMakerAnalyzer", "LiquidityAnalyzerSMC", "SupplyDemandAnalyzer",
    
    # VSA
    "VSAAnalyzer", "VSAConfidenceCalculator", "VSASignalBuilder",
    "VSASignal", "SpreadAnalysis", "VolumeClimax", "EffortResult",
    "SpreadAnalyzer", "VolumeAnalyzerVSA", "BarAnalyzer",
    "EffortResultAnalyzer", "ConfirmationAnalyzer",
    
    # Hybrid
    "FusionEngine", "CrossValidator", "TripleFilter",
    
    # Fundamental
    "NewsImpactAnalyzer", "SentimentAnalyzer", "EconomicCalendar",
    
    # Signal Generation
    "SignalGenerator", "SignalScheduler", "scheduler",
]