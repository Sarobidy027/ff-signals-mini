"""Validateur croisé des 4 stratégies."""
from typing import Dict, Any, Optional, List


class CrossValidator:
    """Validation croisée ICT + SMC + VSA + Fondamental."""
    
    def validate(
        self, ict_signal=None, smc_signal=None, vsa_signal=None,
        fundamental_ok: bool = True, sentiment: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        
        signals = []
        
        if ict_signal and self._is_valid(ict_signal):
            signals.append({
                "source": "ICT", "direction": self._extract_dir(ict_signal),
                "confidence": self._extract_conf(ict_signal),
                "entry": self._extract_entry(ict_signal),
                "sl": self._extract_sl(ict_signal), "tp": self._extract_tp(ict_signal),
            })
        
        if smc_signal and self._is_valid(smc_signal):
            signals.append({
                "source": "SMC", "direction": self._extract_dir(smc_signal),
                "confidence": self._extract_conf(smc_signal),
                "entry": self._extract_entry(smc_signal),
                "sl": self._extract_sl(smc_signal), "tp": self._extract_tp(smc_signal),
            })
        
        if vsa_signal and self._is_valid(vsa_signal):
            signals.append({
                "source": "VSA", "direction": self._extract_dir(vsa_signal),
                "confidence": self._extract_conf(vsa_signal),
                "entry": self._extract_entry(vsa_signal),
                "sl": self._extract_sl(vsa_signal), "tp": self._extract_tp(vsa_signal),
            })
        
        if fundamental_ok:
            signals.append({
                "source": "FUNDAMENTAL", "direction": sentiment.get("sentiment", "NEUTRAL") if sentiment else "NEUTRAL",
                "confidence": sentiment.get("confidence", 50) if sentiment else 50,
            })
        
        # Règles de validation
        if len(signals) < 3:
            return {"valid": False, "reason": f"Seulement {len(signals)} signaux"}
        
        ict_present = any(s["source"] == "ICT" for s in signals)
        if not ict_present:
            return {"valid": False, "reason": "ICT non validé"}
        
        directions = [s["direction"] for s in signals if s["direction"] != "NEUTRAL"]
        if len(set(directions)) > 1:
            return {"valid": False, "reason": "Directions divergentes"}
        
        if not directions:
            return {"valid": False, "reason": "Aucune direction claire"}
        
        direction = directions[0]
        entry = self._optimize_entry(signals)
        sl = self._optimize_sl(signals, direction)
        tp = self._optimize_tp(signals)
        
        convergence = self._calc_convergence(signals)
        
        return {
            "valid": True, "direction": "BUY" if direction == "BULLISH" else "SELL",
            "entry_price": entry, "stop_loss": sl, "take_profit": tp,
            "convergence_score": convergence,
            "contributing_strategies": [s["source"] for s in signals],
        }
    
    def _is_valid(self, signal) -> bool:
        if signal is None:
            return False
        conf = self._extract_conf(signal)
        return conf >= 60
    
    def _extract_dir(self, signal) -> str:
        if hasattr(signal, 'direction'):
            val = signal.direction
            return val.value if hasattr(val, 'value') else str(val)
        return "NEUTRAL"
    
    def _extract_conf(self, signal) -> float:
        if hasattr(signal, 'confidence'):
            return float(signal.confidence)
        if hasattr(signal, 'validation_score'):
            return float(signal.validation_score)
        return 50.0
    
    def _extract_entry(self, signal) -> Optional[float]:
        return float(signal.entry_price) if hasattr(signal, 'entry_price') else None
    
    def _extract_sl(self, signal) -> Optional[float]:
        return float(signal.stop_loss) if hasattr(signal, 'stop_loss') else None
    
    def _extract_tp(self, signal) -> Optional[float]:
        return float(signal.take_profit) if hasattr(signal, 'take_profit') else None
    
    def _optimize_entry(self, signals: List[Dict]) -> float:
        entries = [s["entry"] for s in signals if s.get("entry")]
        if not entries:
            return 0.0
        weights = [s["confidence"] for s in signals if s.get("entry")]
        total = sum(weights)
        return sum(e * w for e, w in zip(entries, weights)) / total if total > 0 else entries[0]
    
    def _optimize_sl(self, signals: List[Dict], direction: str) -> float:
        sls = [s["sl"] for s in signals if s.get("sl")]
        if not sls:
            return 0.0
        return max(sls) if direction in ["BULLISH", "BUY"] else min(sls)
    
    def _optimize_tp(self, signals: List[Dict]) -> float:
        tps = [s["tp"] for s in signals if s.get("tp")]
        return sum(tps) / len(tps) if tps else 0.0
    
    def _calc_convergence(self, signals: List[Dict]) -> float:
        if len(signals) >= 4:
            base = 100
        elif len(signals) == 3:
            base = 85
        else:
            base = 70
        avg_conf = sum(s["confidence"] for s in signals) / len(signals)
        return min(base * (avg_conf / 100), 100)