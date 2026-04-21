"""Calculateur de confiance SMC - Utilise tous les sous-modules."""
from typing import Dict, Any


class SMCConfidenceCalculator:
    """Calcule le score de confiance basé sur tous les composants SMC."""
    
    WEIGHTS = {
        "wyckoff": 0.15,
        "volume": 0.15,
        "patterns": 0.20,
        "order_flow": 0.15,
        "market_maker": 0.15,
        "liquidity": 0.10,
        "supply_demand": 0.10,
    }
    
    @classmethod
    def compute(cls, data: Dict[str, Any]) -> float:
        """Calcule la confiance à partir de toutes les données."""
        scores = {}
        
        # 1. Wyckoff
        scores["wyckoff"] = cls._score_wyckoff(
            data.get("wyckoff_phase"), data.get("volume_confirm")
        )
        
        # 2. Volume
        scores["volume"] = cls._score_volume(
            data.get("volume_profile"), data.get("climax"), data.get("divergence")
        )
        
        # 3. Patterns
        scores["patterns"] = cls._score_patterns(
            data.get("spring_upthrust"), data.get("absorptions")
        )
        
        # 4. Order Flow
        scores["order_flow"] = cls._score_order_flow(
            data.get("delta"), data.get("delta_div"), data.get("footprint")
        )
        
        # 5. Market Maker
        scores["market_maker"] = cls._score_market_maker(
            data.get("mmm"), data.get("stop_hunts_mm"), data.get("liquidity_grabs")
        )
        
        # 6. Liquidité
        scores["liquidity"] = cls._score_liquidity(data.get("liquidity_data"))
        
        # 7. Supply/Demand
        scores["supply_demand"] = cls._score_supply_demand(data.get("fresh_zones"))
        
        total = sum(scores.get(k, 0) * w for k, w in cls.WEIGHTS.items())
        return min(total, 100)
    
    @classmethod
    def _score_wyckoff(cls, phase, confirm) -> float:
        score = 40
        if phase:
            score += 30
            if confirm and confirm.get("confirmed"):
                score += 20
        return min(score, 100)
    
    @classmethod
    def _score_volume(cls, profile, climax, divergence) -> float:
        score = 50
        if profile:
            if profile.get("trend") != "stable":
                score += 15
            if profile.get("spike", {}).get("detected"):
                score += 15
        if climax:
            score += 15
        if divergence and divergence.get("detected"):
            score += 10
        return min(score, 100)
    
    @classmethod
    def _score_patterns(cls, spring_upthrust, absorptions) -> float:
        score = 30
        if spring_upthrust:
            score += 40
            if spring_upthrust.volume_confirmation:
                score += 20
        if absorptions:
            score += min(len(absorptions) * 10, 20)
        return min(score, 100)
    
    @classmethod
    def _score_order_flow(cls, delta, delta_div, footprint) -> float:
        score = 50
        if delta:
            if abs(delta.get("value", 0)) > 0.2:
                score += 20
        if delta_div and delta_div.get("detected"):
            score += 15
        if footprint and footprint.get("imbalance"):
            score += 10
        return min(score, 100)
    
    @classmethod
    def _score_market_maker(cls, mmm, stop_hunts, liquidity_grabs) -> float:
        score = 40
        if mmm:
            score += 35
        if stop_hunts:
            score += min(len(stop_hunts) * 10, 20)
        if liquidity_grabs:
            score += min(len(liquidity_grabs) * 10, 20)
        return min(score, 100)
    
    @classmethod
    def _score_liquidity(cls, liquidity_data) -> float:
        if not liquidity_data:
            return 40
        score = 50
        pools = liquidity_data.get("pools", [])
        if pools:
            score += min(len(pools) * 10, 30)
        return min(score, 100)
    
    @classmethod
    def _score_supply_demand(cls, fresh_zones) -> float:
        if not fresh_zones:
            return 40
        score = 50
        demand = [z for z in fresh_zones if z.zone_type == "DEMAND"]
        supply = [z for z in fresh_zones if z.zone_type == "SUPPLY"]
        if demand:
            score += 20
        if supply:
            score += 20
        return min(score, 100)