"""Shared checks prevent publishing a music-enabled mod without its soundtrack."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "tools" / "music"
OUTPUT = ROOT / "build" / "music"
STATE = OUTPUT / "build-state.json"


def tracks():
    return json.loads((SOURCE / "tracks.json").read_text(encoding="utf-8"))


def filename(track):
    # The engine recognizes this suffix and advances after the track ends.
    return track["id"] + "[noloop].ogg"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_digest():
    result = hashlib.sha256()
    inputs = [path for path in SOURCE.iterdir() if path.suffix in {".py", ".json"}]
    inputs.extend([ROOT / "tools" / "build_music.py", ROOT / "uv.lock", ROOT / ".python-version"])
    for path in sorted(inputs):
        if path.is_file():
            result.update(path.relative_to(ROOT).as_posix().encode("utf-8") + b"\0" + path.read_bytes())
    return result.hexdigest()


def verified_audio():
    instruction = "Run uv run --locked python tools/build_music.py before packaging."
    if not STATE.is_file():
        raise RuntimeError("Soundtrack has not been built. " + instruction)
    state = json.loads(STATE.read_text(encoding="utf-8"))
    if state.get("source_sha256") != source_digest():
        raise RuntimeError("Soundtrack sources changed since the last build. " + instruction)
    expected = {filename(t) for t in tracks()}
    if set(state.get("files", {})) != expected:
        raise RuntimeError("Soundtrack manifest is incomplete. " + instruction)
    paths = []
    for name in sorted(expected):
        path = OUTPUT / name
        if not path.is_file() or digest(path) != state["files"][name]:
            raise RuntimeError(f"Soundtrack missing or altered: {name}. " + instruction)
        paths.append(path)
    return paths
