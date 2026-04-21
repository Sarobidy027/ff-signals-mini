"""Killzone manager."""
from datetime import datetime, time, timedelta
from typing import Optional, Dict, Any


class Killzone:
    ZONES = {
        "ASIAN": (time(0, 0), time(2, 0)),
        "LONDON": (time(7, 0), time(9, 0)),
        "NY_OPEN": (time(12, 0), time(14, 0)),
        "LONDON_CLOSE": (time(15, 0), time(17, 0)),
    }
    
    @classmethod
    def get_current(cls, now: Optional[datetime] = None) -> Optional[Dict]:
        now = now or datetime.utcnow()
        t = now.time()
        for name, (start, end) in cls.ZONES.items():
            if start <= t <= end:
                return {"name": name, "start": start, "end": end, "active": True}
        return None
    
    @classmethod
    def is_active(cls) -> bool:
        return cls.get_current() is not None
    
    @classmethod
    def is_london_session(cls) -> bool:
        zone = cls.get_current()
        return zone is not None and zone["name"] in ["LONDON", "LONDON_CLOSE"]
    
    @classmethod
    def is_ny_session(cls) -> bool:
        zone = cls.get_current()
        return zone is not None and zone["name"] == "NY_OPEN"
    
    @classmethod
    def get_next(cls, now: Optional[datetime] = None) -> Dict:
        now = now or datetime.utcnow()
        t = now.time()
        for name, (start, end) in sorted(cls.ZONES.items(), key=lambda x: x[1][0]):
            if start > t:
                return {"name": name, "start": start, "end": end}
        first = list(cls.ZONES.items())[0]
        return {"name": first[0], "start": first[1][0], "end": first[1][1]}
    
    @classmethod
    def time_until_next(cls) -> float:
        now = datetime.utcnow()
        next_kz = cls.get_next(now)
        kz_start = datetime.combine(now.date(), next_kz["start"])
        if kz_start <= now:
            kz_start = datetime.combine(now.date() + timedelta(days=1), next_kz["start"])
        return (kz_start - now).total_seconds() / 3600