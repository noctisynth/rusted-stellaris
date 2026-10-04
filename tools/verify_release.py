"""Reject stale or altered release assets downloaded from the quality job."""
import hashlib
import json
import tomllib
from pathlib import Path
import subprocess
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
archive = ROOT / "build" / "rusted-stellaris-dev.rwmod"
version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
checksum = f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n"
if (ROOT / "build" / "SHA256SUMS.txt").read_text(encoding="utf-8") != checksum:
    raise SystemExit("Release archive checksum mismatch")
with ZipFile(archive) as package:
    if json.loads(package.read("version.json")) != {"version": version, "commit": commit}:
        raise SystemExit("Release archive was built for a different version or commit")
info = (ROOT / "build" / "BUILD-INFO.txt").read_text(encoding="utf-8")
if not info.startswith(f"Version: {version}\nCommit: {commit}\n"):
    raise SystemExit("Release build information does not match this checkout")
print(f"Verified release assets: {version} ({commit[:12]})")
