"""
Utilitaires de validation.
"""
from typing import List, Optional
from app.models.signal import Signal


def validate_price(price: float, instrument: str) -> bool:
    """Valide qu'un prix est positif et cohérent."""
    if price <= 0:
        return False
    
    if "JPY" in instrument:
        return 50 <= price <= 200
    elif "BTC" in instrument:
        return 1000 <= price <= 1000000
    elif "ETH" in instrument:
        return 100 <= price <= 10000
    elif any(c in instrument for c in ["EUR", "GBP", "AUD", "NZD", "CAD", "CHF"]):
        return 0.1 <= price <= 10.0
    
    return True


def validate_signal(signal: Signal) -> List[str]:
    """Valide un signal et retourne les erreurs."""
    errors = []
    
    if not validate_price(signal.entry_price, signal.instrument):
        errors.append(f"Prix d'entrée invalide: {signal.entry_price}")
    
    if not validate_price(signal.stop_loss, signal.instrument):
        errors.append(f"Stop loss invalide: {signal.stop_loss}")
    
    if not validate_price(signal.take_profit, signal.instrument):
        errors.append(f"Take profit invalide: {signal.take_profit}")
    
    if signal.direction.value == "BUY":
        if signal.stop_loss >= signal.entry_price:
            errors.append("SL doit être inférieur au prix d'entrée pour un BUY")
        if signal.take_profit <= signal.entry_price:
            errors.append("TP doit être supérieur au prix d'entrée pour un BUY")
    else:
        if signal.stop_loss <= signal.entry_price:
            errors.append("SL doit être supérieur au prix d'entrée pour un SELL")
        if signal.take_profit >= signal.entry_price:
            errors.append("TP doit être inférieur au prix d'entrée pour un SELL")
    
    if signal.confidence < 0 or signal.confidence > 100:
        errors.append(f"Confiance invalide: {signal.confidence}")
    
    return errors


def validate_rr_ratio(entry: float, sl: float, tp: float, direction: str) -> bool:
    """Valide que le ratio R:R est acceptable."""
    risk = abs(entry - sl)
    reward = abs(tp - entry)
    
    if risk <= 0:
        return False
    
    rr = reward / risk
    return rr >= 1.5