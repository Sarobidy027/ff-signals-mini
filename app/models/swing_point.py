"""
Modèle Swing Point.
"""
from typing import Literal
from datetime import datetime

from pydantic import BaseModel


class SwingPoint(BaseModel):
    """Point de swing (haut ou bas)."""
    index: int
    price: float
    timestamp: datetime
    point_type: Literal["HIGH", "LOW"]
    strength: int = 1
    is_fractal: bool = False
    volume: float = 0.0