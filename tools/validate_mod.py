"""Check local unit references and sprite files before loading the game."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1] / "mod" / "rusted-stellaris"
FILES = sorted((ROOT / "units").glob("*.ini"))
UNITS = {}
ERRORS = []
RESOURCE_TEMPLATE = ROOT / "all-units.template"


def fields(path):
    section = ""
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            continue
        if ":" not in line:
            ERRORS.append(f"{path.name}:{number}: missing ':'")
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        yield section, key, value


for path in FILES:
    entries = list(fields(path))
    names = [v for s, k, v in entries if s == "core" and k == "name"]
    if len(names) != 1:
        ERRORS.append(f"{path.name}: expected one [core] name")
        continue
    if names[0] in UNITS:
        ERRORS.append(f"{path.name}: duplicate unit name {names[0]}")
    UNITS[names[0]] = (path, entries)

resources = set()
if RESOURCE_TEMPLATE.is_file():
    resources = {
        section.removeprefix("global_resource_")
        for section, _, _ in fields(RESOURCE_TEMPLATE)
        if section.startswith("global_resource_")
    }
    if resources != {"energy", "minerals", "alloys", "science", "unity", "strategic"}:
        ERRORS.append(f"resource template has unexpected resources: {sorted(resources)}")
else:
    ERRORS.append("missing all-units.template")

for name, (path, entries) in UNITS.items():
    sections = {s for s, _, _ in entries}
    for required in ("core", "graphics", "attack", "movement"):
        if required not in sections:
            ERRORS.append(f"{path.name}: missing [{required}]")
    for section, key, value in entries:
        if section == "graphics" and key in ("image", "image_wreak"):
            if not (path.parent / value).is_file():
                ERRORS.append(f"{path.name}: missing sprite {value}")
        if section == "core" and re.match(r"(?:canBuild|builtFrom)_\d+_name", key):
            for target in (v.strip() for v in value.split(",")):
                if target.startswith("rs") and target not in UNITS:
                    ERRORS.append(f"{path.name}: unknown unit {target}")
        if section == "core" and key in ("price", "generation_resources") and "=" in value:
            for pair in value.split(","):
                resource = pair.split("=", 1)[0].strip()
                if resource not in resources | {"credits"}:
                    ERRORS.append(f"{path.name}: unknown resource {resource}")

if not (ROOT / "mod-info.txt").is_file():
    ERRORS.append("missing mod-info.txt")

if ERRORS:
    print("\n".join(ERRORS), file=sys.stderr)
    raise SystemExit(1)
print(f"Validated {len(UNITS)} units and local sprite references")
