"""Package the source directory as a Rusted Warfare .rwmod archive."""

from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from music.build_support import verified_audio

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mod" / "rusted-stellaris"
DEST = ROOT / "build" / "rusted-stellaris-dev.rwmod"
MUSIC = verified_audio()
DEST.parent.mkdir(parents=True, exist_ok=True)

with ZipFile(DEST, "w", ZIP_DEFLATED) as archive:
    for path in sorted(SOURCE.rglob("*")):
        if path.is_file():
            archive.write(path, path.relative_to(SOURCE).as_posix())
    for path in sorted((ROOT / "maps").glob("*")):
        if path.is_file():
            archive.write(path, path.name)
    for path in MUSIC:
        archive.write(path, "music/" + path.name)

with ZipFile(DEST) as archive:
    assert "mod-info.txt" in archive.namelist()
    assert "all-units.template" in archive.namelist()
    source_units = {path.relative_to(SOURCE).as_posix() for path in (SOURCE / "units").glob("*.ini") if not path.name.startswith("_")}
    archive_units = {name for name in archive.namelist() if name.startswith("units/") and name.endswith(".ini") and not Path(name).name.startswith("_")}
    assert archive_units == source_units
    assert len([name for name in archive.namelist() if name.endswith(".tmx")]) == 3
    assert {name for name in archive.namelist() if name.endswith(".ogg")} == {"music/" + path.name for path in MUSIC}

print(DEST)
