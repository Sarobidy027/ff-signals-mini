"""Analyseur SMC principal - Utilise tous les sous-modules."""
from typing import Optional, List
from datetime import datetime
import uuid
import structlog

from app.data.market_providers import MarketProviderFactory, CandleData
from app.data.instruments import get_current_price, get_spread
from app.data.news import has_major_news
from app.utils.validation_utils import validate_rr_ratio
from app.engine.smc.models import SMCSignal
from app.engine.smc.wyckoff import WyckoffPhases, WyckoffSchematics, VolumeConfirmation
from app.engine.smc.volume import VolumeAnalysis, VolumeClimaxDetector, VolumeDivergence
from app.engine.smc.patterns import SpringDetector, UpthrustDetector, TerminalShakeoutDetector, AbsorptionDetector
from app.engine.smc.order_flow import DeltaAnalyzer, FootprintAnalyzer, POCAnalyzer
from app.engine.smc.market_maker import MarketMakerModels, StopHuntDetector, LiquidityGrabDetector
from app.engine.smc.liquidity_smc import LiquidityPoolsSMC, InducementDetectorSMC, StopHuntDetectorSMC
from app.engine.smc.supply_demand import SupplyDemandZones, FreshZones, ZoneStrength
from app.engine.smc.confidence import SMCConfidenceCalculator
from app.engine.smc.signal_builder import SMCSignalBuilder
from app.core.config import settings

logger = structlog.get_logger()


class SMCAnalyzer:
    """Analyseur Smart Money Concept complet - Utilise tous les sous-modules."""
    
    def __init__(self, instrument: str, timeframe: str = "15min"):
        self.instrument = instrument
        self.timeframe = timeframe
        self.candles: List[CandleData] = []
        self._loaded = False
        
        # Sous-modules
        self.wyckoff_phases = None
        self.wyckoff_schematics = None
        self.volume_confirmation = None
        self.volume_analysis = None
        self.volume_climax = None
        self.volume_divergence = None
        self.spring_detector = None
        self.upthrust_detector = None
        self.shakeout_detector = None
        self.absorption_detector = None
        self.delta_analyzer = None
        self.footprint_analyzer = None
        self.poc_analyzer = None
        self.mm_models = None
        self.stop_hunt_detector = None
        self.liquidity_grab_detector = None
        self.liquidity_pools = None
        self.inducement_detector = None
        self.stop_hunt_smc = None
        self.sd_zones = None
        self.fresh_zones = None
        self.zone_strength = None
    
    def _init_modules(self):
        """Initialise tous les sous-modules."""
        self.wyckoff_phases = WyckoffPhases()
        self.wyckoff_schematics = WyckoffSchematics()
        self.volume_confirmation = VolumeConfirmation()
        self.volume_analysis = VolumeAnalysis(self.candles)
        self.volume_climax = VolumeClimaxDetector(self.candles)
        self.volume_divergence = VolumeDivergence()
        self.spring_detector = SpringDetector()
        self.upthrust_detector = UpthrustDetector()
        self.shakeout_detector = TerminalShakeoutDetector()
        self.absorption_detector = AbsorptionDetector()
        self.delta_analyzer = DeltaAnalyzer()
        self.footprint_analyzer = FootprintAnalyzer()
        self.poc_analyzer = POCAnalyzer()
        self.mm_models = MarketMakerModels()
        self.stop_hunt_detector = StopHuntDetector()
        self.liquidity_grab_detector = LiquidityGrabDetector()
        self.liquidity_pools = LiquidityPoolsSMC()
        self.inducement_detector = InducementDetectorSMC()
        self.stop_hunt_smc = StopHuntDetectorSMC()
        self.sd_zones = SupplyDemandZones()
        self.fresh_zones = FreshZones()
        self.zone_strength = ZoneStrength()
    
    async def load_data(self) -> bool:
        """Charge les données de marché."""
        try:
            self.candles = await MarketProviderFactory.get_candles(
                self.instrument, self.timeframe, count=200
            )
            self._loaded = len(self.candles) >= 50
            if self._loaded:
                self._init_modules()
                logger.debug("smc_data_loaded", instrument=self.instrument, candles=len(self.candles))
            return self._loaded
        except Exception as e:
            logger.error("smc_load_failed", instrument=self.instrument, error=str(e))
            return False
    
    async def analyze(self) -> Optional[SMCSignal]:
        """Analyse SMC complète utilisant tous les sous-modules."""
        if not self._loaded and not await self.load_data():
            return None
        if len(self.candles) < 50:
            return None
        
        current_price = await get_current_price(self.instrument)
        if current_price <= 0:
            current_price = self.candles[-1].close
        
        spread = get_spread(self.instrument)
        
        # 1. Wyckoff Analysis
        wyckoff_phase = self.wyckoff_phases.detect_phase(self.candles)
        wyckoff_points = self.wyckoff_schematics.identify_points(self.candles)
        volume_confirm = self.volume_confirmation.confirm_phase(
            self.candles, wyckoff_phase.phase_type.value if wyckoff_phase else "UNKNOWN"
        )
        
        # 2. Volume Analysis
        volume_profile = self.volume_analysis.analyze()
        climax = self.volume_climax.detect()
        divergence = self.volume_divergence.detect(self.candles)
        
        # 3. Support/Résistance pour Springs/Upthrusts
        support, resistance = self._get_support_resistance()
        
        # 4. Patterns
        spring = self.spring_detector.detect(self.candles, support)
        upthrust = self.upthrust_detector.detect(self.candles, resistance)
        shakeout = self.shakeout_detector.detect(self.candles)
        absorptions = self.absorption_detector.detect(self.candles)
        
        spring_upthrust = spring or upthrust or shakeout
        
        # 5. Order Flow
        delta = self.delta_analyzer.calculate(self.candles)
        delta_div = self.delta_analyzer.delta_divergence(self.candles)
        footprint = self.footprint_analyzer.analyze(self.candles)
        poc = self.poc_analyzer.find_poc(self.candles)
        
        # 6. Market Maker Models
        mmm = self.mm_models.detect(self.candles)
        stop_hunts_mm = self.stop_hunt_detector.detect(self.candles)
        liquidity_grabs = self.liquidity_grab_detector.detect(self.candles)
        
        # 7. Liquidité SMC
        liquidity_data = self.liquidity_pools.find_pools(self.candles)
        inducements = self.inducement_detector.detect(self.candles)
        stop_hunts = self.stop_hunt_smc.detect(self.candles)
        
        # 8. Supply/Demand Zones
        all_zones = self.sd_zones.find_all(self.candles)
        fresh_zones = self.fresh_zones.filter_fresh(all_zones, self.candles)
        strongest_demand = self.zone_strength.get_strongest(fresh_zones, self.candles, "DEMAND")
        strongest_supply = self.zone_strength.get_strongest(fresh_zones, self.candles, "SUPPLY")
        
        # 9. Calcul de confiance (utilise tous les composants)
        confidence_data = {
            "wyckoff_phase": wyckoff_phase,
            "volume_confirm": volume_confirm,
            "volume_profile": volume_profile,
            "climax": climax,
            "divergence": divergence,
            "spring_upthrust": spring_upthrust,
            "absorptions": absorptions,
            "delta": delta,
            "delta_div": delta_div,
            "footprint": footprint,
            "mmm": mmm,
            "stop_hunts_mm": stop_hunts_mm,
            "liquidity_grabs": liquidity_grabs,
            "liquidity_data": liquidity_data,
            "fresh_zones": fresh_zones,
        }
        
        confidence = SMCConfidenceCalculator.compute(confidence_data)
        
        if confidence < 70:
            logger.debug("smc_confidence_low", instrument=self.instrument, confidence=confidence)
            return None
        
        # 10. Fondamental
        fundamental_ok = not await has_major_news(self.instrument, 2)
        if not fundamental_ok:
            confidence = max(confidence - 10, 0)
        
        # 11. Construire le signal
        builder = SMCSignalBuilder()
        signal = builder.build(
            instrument=self.instrument, timeframe=self.timeframe,
            confidence=confidence, wyckoff_phase=wyckoff_phase,
            spring_upthrust=spring_upthrust, sd_zones=fresh_zones,
            mmm=mmm, current_price=current_price,
        )
        
        if not validate_rr_ratio(signal.entry_price, signal.stop_loss, signal.take_profit, signal.direction.value):
            return None
        
        logger.info("smc_signal_generated", instrument=self.instrument,
                   direction=signal.direction.value, confidence=confidence,
                   wyckoff=wyckoff_phase.phase_type.value if wyckoff_phase else "NONE",
                   pattern=spring_upthrust.pattern_type.value if spring_upthrust else "NONE")
        
        return signal
    
    def _get_support_resistance(self):
        """Calcule support et résistance."""
        recent = self.candles[-50:]
        highs = [c.high for c in recent]
        lows = [c.low for c in recent]
        
        support = self._find_cluster(lows, "low")
        resistance = self._find_cluster(highs, "high")
        
        return support, resistance
    
    def _find_cluster(self, prices: List[float], direction: str) -> float:
        if not prices:
            return 0.0
        sorted_prices = sorted(prices)
        clusters = []
        current = [sorted_prices[0]]
        for p in sorted_prices[1:]:
            if abs(p - current[-1]) / current[-1] < 0.002:
                current.append(p)
            else:
                if len(current) >= 2:
                    clusters.append(current)
                current = [p]
        if len(current) >= 2:
            clusters.append(current)
        if clusters:
            best = max(clusters, key=len)
            return sum(best) / len(best)
        return min(prices) if direction == "low" else max(prices)