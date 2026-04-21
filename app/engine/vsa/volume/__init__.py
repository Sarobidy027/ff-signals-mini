"""Volume VSA Module."""
from app.engine.vsa.volume.relative import RelativeVolumeAnalyzer
from app.engine.vsa.volume.stopping import StoppingVolumeDetector
from app.engine.vsa.volume.climax import ClimaxDetector

__all__ = ["RelativeVolumeAnalyzer", "StoppingVolumeDetector", "ClimaxDetector"]