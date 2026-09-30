"""Package the source directory as a Rusted Warfare .rwmod archive."""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mod" / "rusted-stellaris"
DEST = ROOT / "build" / "rusted-stellaris-dev.rwmod"
DEST.parent.mkdir(parents=True, exist_ok=True)

with ZipFile(DEST, "w", ZIP_DEFLATED) as archive:
    for path in sorted(SOURCE.rglob("*")):
        if path.is_file():
            archive.write(path, path.relative_to(SOURCE).as_posix())
    for path in sorted((ROOT / "maps").glob("*")):
        if path.is_file():
            archive.write(path, path.name)

with ZipFile(DEST) as archive:
    assert "mod-info.txt" in archive.namelist()
    assert "all-units.template" in archive.namelist()
    assert len([name for name in archive.namelist() if name.endswith(".ini")]) == 10
    assert len([name for name in archive.namelist() if name.endswith(".tmx")]) == 3

print(DEST)
