"""Keep audio and downloaded samples outside the versioned source tree."""
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
PROJECT = SOURCE.parents[1]
WORK = PROJECT / "work" / "music" / "astra"
INSTRUMENTS = SOURCE / "instruments.json"
WORK.mkdir(parents=True, exist_ok=True)
