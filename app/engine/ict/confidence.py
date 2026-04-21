"""Calculateur de confiance ICT."""
from typing import Dict, Any, List, Optional


class ConfidenceCalculator:
    """Calcule le score de confiance ICT."""
    
    WEIGHTS = {
        "htf": 0.20, "ob": 0.25, "fvg": 0.15,
        "liquidity": 0.15, "killzone": 0.10, "fundamental": 0.15,
    }
    
    @classmethod
    def compute(
        cls, htf_bias: Dict, mss: Optional[Dict], order_blocks: List, fvgs: List,
        liquidity_pools: List, in_killzone: bool, fundamental_ok: bool,
    ) -> float:
        scores = {}
        scores["htf"] = htf_bias.get("strength", 0.5) * 100 if htf_bias.get("direction") != "NEUTRAL" else 30
        
        active_obs = [ob for ob in order_blocks if ob.is_active]
        scores["ob"] = min(len(active_obs) * 20 + 30, 100) if active_obs else 20
        
        unfilled = [f for f in fvgs if not f.is_filled]
        scores["fvg"] = min(len(unfilled) * 20 + 30, 100) if unfilled else 20
        
        scores["liquidity"] = min(len(liquidity_pools) * 20 + 30, 100) if liquidity_pools else 30
        
        scores["killzone"] = 100 if in_killzone else 0
        scores["fundamental"] = 100 if fundamental_ok else 0
        
        if mss:
            scores["mss_bonus"] = 10
            total = sum(scores.get(k, 0) * w for k, w in cls.WEIGHTS.items()) + 10
        else:
            total = sum(scores.get(k, 0) * w for k, w in cls.WEIGHTS.items())
        
        return min(total, 100)