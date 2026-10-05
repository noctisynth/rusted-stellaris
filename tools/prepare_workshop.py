"""Stage a verified .rwmod for updating the existing Steam Workshop item.

This command has no Steam credentials and does not upload anything.
"""

from argparse import ArgumentParser
import json
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from verify_release import ROOT, archive as archive_path  # Verifies hash, version, and source commit on import.

APP_ID = "647960"
ITEM_ID = "3813493737"


def vdf_value(value: str) -> str:
    if any(ord(char) < 32 for char in value):
        raise ValueError("VDF values must not contain control characters")
    return value.replace("\\", "\\\\").replace('"', '\\"')


def stage(destination: Path, change_note: str) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    content = destination / "content"
    content.mkdir(exist_ok=True)
    if any(content.iterdir()):
        raise ValueError("Workshop staging directory must be empty")
    with ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Archive contains duplicate paths")
        if "mod-info.txt" not in names or "version.json" not in names:
            raise ValueError("Archive does not contain the expected mod root")
        if len([name for name in names if name.endswith(".ogg")]) != 4:
            raise ValueError("Archive must contain four soundtrack files")
        for item in archive.infolist():
            path = PurePosixPath(item.filename)
            if (path.is_absolute() or ".." in path.parts or "\\" in item.filename
                    or not path.parts or item.is_dir()):
                raise ValueError(f"Unsafe archive path: {item.filename}")
            target = content.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(item))
    (content / "steam.dat").write_text(f"[steam]\nid: {ITEM_ID}\n", encoding="utf-8")
    preview = content / "mod-thumbnail.png"
    lines = [
        '"workshopitem"', "{",
        f'    "appid" "{APP_ID}"',
        f'    "publishedfileid" "{ITEM_ID}"',
        f'    "contentfolder" "{vdf_value(str(content.resolve()))}"',
        f'    "changenote" "{vdf_value(change_note)}"',
    ]
    if preview.is_file():
        lines.append(f'    "previewfile" "{vdf_value(str(preview.resolve()))}"')
    lines.append("}")
    output = destination / "workshop.vdf"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "build" / "workshop")
    parser.add_argument("--change-note", required=True)
    args = parser.parse_args()
    print(stage(args.output, args.change_note))
