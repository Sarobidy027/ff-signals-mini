"""Triple filtre pour signaux haute qualité."""
from typing import Dict, Any
from app.engine.ict.time_price import Killzone


class TripleFilter:
    """Filtre structurel, temporel et prix."""
    
    def apply(self, validation: Dict, instrument: str) -> Dict[str, Any]:
        score = 0
        passed = []
        
        # Filtre 1 : Structurel
        if validation["convergence_score"] >= 70:
            score += 40
            passed.append("structural")
        
        # Filtre 2 : Temporel
        if Killzone.is_active():
            score += 30
            passed.append("temporal")
        
        # Filtre 3 : Prix
        rr = self._calc_rr(validation)
        if rr >= 1.5:
            score += 30
            passed.append("price")
        
        final_conf = min(validation["convergence_score"] * (score / 100), 100)
        entry_delay = 1 if len(passed) == 3 else (3 if len(passed) >= 2 else 5)
        
        return {
            "passed": len(passed) >= 2 and "structural" in passed,
            "filters_passed": passed, "filter_score": score,
            "final_confidence": final_conf, "entry_delay": entry_delay,
        }
    
    def _calc_rr(self, v: dict) -> float:
        entry = v.get("entry_price", 0)
        sl = v.get("stop_loss", 0)
        tp = v.get("take_profit", 0)
        if entry == 0 or sl == 0 or tp == 0:
            return 1.0
        risk = abs(entry - sl)
        reward = abs(tp - entry)
        return reward / risk if risk > 0 else 1.0