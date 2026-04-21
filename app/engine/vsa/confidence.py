"""Calculateur de confiance VSA - Utilise tous les sous-modules."""
from typing import Dict, Any


class VSAConfidenceCalculator:
    """Calcule le score de confiance basé sur tous les composants VSA."""
    
    WEIGHTS = {
        "spread": 0.15,
        "volume": 0.25,
        "bars": 0.20,
        "effort_result": 0.15,
        "confirmation": 0.15,
        "reversal": 0.10,
    }
    
    @classmethod
    def compute(cls, data: Dict[str, Any]) -> float:
        scores = {}
        
        scores["spread"] = cls._score_spread(
            data.get("spread_result"), data.get("narrows"), data.get("wides")
        )
        scores["volume"] = cls._score_volume(
            data.get("volume_result"), data.get("stopping"), data.get("climax")
        )
        scores["bars"] = cls._score_bars(data.get("bar_signal"))
        scores["effort_result"] = cls._score_effort(
            data.get("effort_result"), data.get("absorptions")
        )
        scores["confirmation"] = cls._score_confirmation(data.get("trend_confirm"))
        scores["reversal"] = cls._score_reversal(data.get("reversal"))
        
        total = sum(scores.get(k, 0) * w for k, w in cls.WEIGHTS.items())
        return min(total, 100)
    
    @classmethod
    def _score_spread(cls, spread, narrows, wides) -> float:
        score = 50
        if spread:
            if spread.spread_type in ["WIDE", "ULTRA_WIDE"]:
                score += 20
            elif spread.spread_type == "NARROW":
                score += 10
        if narrows:
            score += min(len(narrows) * 5, 15)
        if wides:
            score += min(len(wides) * 5, 15)
        return min(score, 100)
    
    @classmethod
    def _score_volume(cls, volume, stopping, climax) -> float:
        score = 40
        if volume:
            if volume.get("level") in ["HIGH", "VERY_HIGH"]:
                score += 25
            if volume.get("trend") != "stable":
                score += 10
        if stopping:
            score += 25
        if climax:
            score += 25
        return min(score, 100)
    
    @classmethod
    def _score_bars(cls, bar) -> float:
        if not bar:
            return 30
        score = 60
        score += bar.get("confidence", 0) * 0.3
        return min(score, 100)
    
    @classmethod
    def _score_effort(cls, effort, absorptions) -> float:
        score = 40
        if effort:
            if effort.signal == "REVERSAL":
                score += 30
            elif effort.signal == "CONTINUATION":
                score += 20
            score += effort.confidence * 0.2
        if absorptions:
            score += min(len(absorptions) * 10, 20)
        return min(score, 100)
    
    @classmethod
    def _score_confirmation(cls, trend) -> float:
        if not trend:
            return 40
        score = 50
        if trend.get("confirmed"):
            score += 30
        score += trend.get("confidence", 0) * 0.2
        return min(score, 100)
    
    @classmethod
    def _score_reversal(cls, reversal) -> float:
        if not reversal:
            return 30
        score = 60
        score += reversal.get("confidence", 0) * 0.3
        return min(score, 100)