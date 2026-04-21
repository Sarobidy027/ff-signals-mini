"""Gap detector."""
from typing import List, Dict, Any
from app.data.market_providers import CandleData


class GapDetector:
    @staticmethod
    def detect_gaps(candles: List[CandleData]) -> List[Dict[str, Any]]:
        gaps = []
        for i in range(1, len(candles)):
            prev_close = candles[i-1].close
            curr_open = candles[i].open
            
            if curr_open > prev_close:
                gap_size = curr_open - prev_close
                gaps.append({
                    "type": "GAP_UP", "timestamp": candles[i].timestamp,
                    "prev_close": prev_close, "curr_open": curr_open,
                    "gap_size": gap_size, "gap_percent": (gap_size / prev_close) * 100,
                    "filled": False,
                })
            elif curr_open < prev_close:
                gap_size = prev_close - curr_open
                gaps.append({
                    "type": "GAP_DOWN", "timestamp": candles[i].timestamp,
                    "prev_close": prev_close, "curr_open": curr_open,
                    "gap_size": gap_size, "gap_percent": (gap_size / prev_close) * 100,
                    "filled": False,
                })
        return gaps
    
    @staticmethod
    def find_unfilled_gaps(candles: List[CandleData]) -> List[Dict[str, Any]]:
        gaps = GapDetector.detect_gaps(candles)
        unfilled = []
        for gap in gaps:
            gap_time = gap["timestamp"]
            filled = False
            for c in candles:
                if c.timestamp <= gap_time:
                    continue
                if gap["type"] == "GAP_UP" and c.low <= gap["prev_close"]:
                    filled = True
                    break
                elif gap["type"] == "GAP_DOWN" and c.high >= gap["prev_close"]:
                    filled = True
                    break
            if not filled:
                unfilled.append(gap)
        return unfilled