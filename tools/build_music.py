"""Build four original tracks into build/music, without versioning audio binaries.

Requires NumPy and ffmpeg/ffprobe on PATH. The first build downloads pinned,
SHA-256-verified CC0 instrument samples from the author's GitHub repository.
Subsequent builds use the ignored local cache. --force regenerates all tracks.
"""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request

from music.build_support import ROOT, SOURCE, OUTPUT, STATE, digest, filename, source_digest, tracks, verified_audio

WORK = ROOT / "work" / "music" / "astra"


def ensure_samples():
    provenance = json.loads((SOURCE / "sample_provenance.json").read_text(encoding="utf-8"))
    mapping = json.loads((SOURCE / "instruments.json").read_text(encoding="utf-8"))
    records = {r["path"]: r for r in provenance["files"]}
    wanted = {r["path"] for instrument in mapping.values() for r in instrument}
    if not wanted <= records.keys():
        raise RuntimeError("An instrument references a sample with no recorded hash")

    def fetch(record):
        relative = PurePosixPath(record["path"])
        if relative.is_absolute() or ".." in relative.parts or "\\" in record["path"]:
            raise ValueError("Unsafe sample path")
        sample_root = (WORK / "samples").resolve()
        target = (sample_root / relative).resolve()
        if not target.is_relative_to(sample_root):
            raise ValueError("Sample path escapes the download cache")
        if target.is_file() and digest(target) == record["sha256"]:
            return
        url = ("https://raw.githubusercontent.com/sgossner/VSCO-2-CE/"
               + provenance["commit"] + "/" + urllib.parse.quote(relative.as_posix()))
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise RuntimeError(f"Downloaded sample hash mismatch: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    with ThreadPoolExecutor(max_workers=6) as pool:
        list(pool.map(fetch, provenance["files"]))
    print(f"Verified {len(provenance['files'])} cached CC0 source files", flush=True)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if not args.force:
        try:
            verified_audio()
        except (RuntimeError, ValueError, OSError):
            pass
        else:
            print("Soundtrack build is current")
            return
    for command in ("ffmpeg", "ffprobe"):
        if shutil.which(command) is None:
            parser.error(f"Install {command} and put it on PATH")
    try:
        import numpy  # noqa: F401
    except ImportError:
        parser.error("Install project dependencies: uv sync --locked")
    WORK.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # An interrupted rebuild must not leave an old manifest claiming success.
    STATE.unlink(missing_ok=True)
    ensure_samples()
    for script in ("render_last_light.py", "compose_three_voyages.py"):
        subprocess.run([sys.executable, str(SOURCE / script)], cwd=ROOT, check=True)
    state = {"source_sha256": source_digest(), "files": {}, "audio": {}}
    for track in tracks():
        output = OUTPUT / filename(track)
        subprocess.run([
            "ffmpeg", "-y", "-v", "error", "-i", str(WORK / (track["id"] + "_mix.wav")),
            "-af", f"volume={track['gain_db']}dB", "-ar", "44100", "-ac", "2",
            "-c:a", "libvorbis", "-q:a", "6", "-metadata", "title=" + track["title"], str(output),
        ], check=True)
        probe = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_name,sample_rate,channels",
            "-of", "json", str(output),
        ], check=True, capture_output=True, text=True)
        info = json.loads(probe.stdout)
        stream = info["streams"][0]
        if (stream["codec_name"] != "vorbis" or stream["channels"] != 2
                or abs(float(info["format"]["duration"]) - track["seconds"]) > .1):
            raise RuntimeError(f"Unexpected encoding or duration: {output.name}")
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(output), "-f", "null", "-"], check=True)
        state["files"][output.name] = digest(output)
        state["audio"][output.name] = info
        print(f"Built {output.name}", flush=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    verified_audio()


if __name__ == "__main__":
    main()
