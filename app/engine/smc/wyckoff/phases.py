"""Détection des phases Wyckoff."""
from typing import List, Optional, Tuple
from datetime import datetime
import numpy as np
from app.data.market_providers import CandleData
from app.engine.smc.models import WyckoffPhase, WyckoffPhaseType


class WyckoffPhases:
    """Analyse des phases d'accumulation et distribution Wyckoff."""
    
    @staticmethod
    def detect_phase(candles: List[CandleData]) -> Optional[WyckoffPhase]:
        if len(candles) < 50:
            return None
        
        trend = WyckoffPhases._determine_trend(candles)
        swings = WyckoffPhases._identify_swings(candles)
        volume_profile = WyckoffPhases._analyze_volume(candles)
        
        phase_type = WyckoffPhases._classify_phase(trend, swings, volume_profile)
        if not phase_type:
            return None
        
        recent = candles[-30:]
        phase_low = min(c.low for c in recent)
        phase_high = max(c.high for c in recent)
        confidence = WyckoffPhases._calculate_confidence(phase_type, swings, volume_profile)
        
        return WyckoffPhase(
            phase_type=phase_type, confidence=confidence,
            start_time=candles[-30].timestamp,
            price_range=(phase_low, phase_high),
            volume_profile=volume_profile["trend"],
            key_levels={"current": candles[-1].close, "high": phase_high, "low": phase_low,
                       "mid": (phase_high + phase_low) / 2},
        )
    
    @staticmethod
    def _determine_trend(candles: List[CandleData]) -> str:
        closes = [c.close for c in candles]
        sma_20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else closes[-1]
        current = closes[-1]
        
        if current > sma_20 > sma_50:
            return "BULLISH"
        elif current < sma_20 < sma_50:
            return "BEARISH"
        return "NEUTRAL"
    
    @staticmethod
    def _identify_swings(candles: List[CandleData]) -> dict:
        swings = {"PS": None, "SC": None, "AR": None, "ST": None,
                 "SOS": None, "SOW": None, "LPS": None, "LPSY": None}
        
        if len(candles) < 50:
            return swings
        
        recent = candles[-50:]
        highs = [c.high for c in recent]
        lows = [c.low for c in recent]
        
        max_idx = highs.index(max(highs))
        min_idx = lows.index(min(lows))
        
        if max_idx > min_idx:
            swings["SC"] = {"price": recent[min_idx].low, "index": min_idx}
        else:
            swings["SC"] = {"price": recent[max_idx].high, "index": max_idx}
        
        return swings
    
    @staticmethod
    def _analyze_volume(candles: List[CandleData]) -> dict:
        volumes = [c.volume for c in candles[-20:]]
        avg = sum(volumes) / len(volumes)
        recent_avg = sum(volumes[-5:]) / 5
        
        trend = "increasing" if recent_avg > avg * 1.2 else \
                ("decreasing" if recent_avg < avg * 0.8 else "stable")
        
        return {"trend": trend, "avg": avg, "recent_avg": recent_avg,
                "climax": max(volumes) > avg * 2.5}
    
    @staticmethod
    def _classify_phase(trend: str, swings: dict, volume: dict) -> Optional[WyckoffPhaseType]:
        if trend == "BEARISH" and volume["trend"] == "increasing" and volume["climax"]:
            return WyckoffPhaseType.ACCUMULATION_A
        elif trend == "NEUTRAL" and volume["trend"] == "decreasing":
            return WyckoffPhaseType.ACCUMULATION_B
        elif trend == "NEUTRAL" and volume["trend"] == "stable":
            return WyckoffPhaseType.ACCUMULATION_C
        elif trend == "BULLISH" and volume["trend"] == "increasing":
            return WyckoffPhaseType.ACCUMULATION_E
        elif trend == "BULLISH" and volume["trend"] == "increasing" and volume["climax"]:
            return WyckoffPhaseType.DISTRIBUTION_A
        elif trend == "NEUTRAL" and volume["trend"] == "decreasing":
            return WyckoffPhaseType.DISTRIBUTION_C
        elif trend == "BEARISH" and volume["trend"] == "increasing":
            return WyckoffPhaseType.DISTRIBUTION_E
        return None
    
    @staticmethod
    def _calculate_confidence(phase: WyckoffPhaseType, swings: dict, volume: dict) -> float:
        base = 60
        if volume["climax"]:
            base += 15
        if swings.get("SC"):
            base += 10
        if volume["trend"] in ["increasing", "decreasing"]:
            base += 10
        return min(base, 95)