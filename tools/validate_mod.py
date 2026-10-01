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
    if any(s == "core" and k == "dont_load" and v.lower() == "true" for s, k, v in entries):
        continue
    names = [v for s, k, v in entries if s == "core" and k == "name"]
    if len(names) != 1:
        ERRORS.append(f"{path.name}: expected one [core] name")
        continue
    if names[0] in UNITS:
        ERRORS.append(f"{path.name}: duplicate unit name {names[0]}")
    UNITS[names[0]] = (path, entries)

resources = set()
if RESOURCE_TEMPLATE.is_file():
    resource_fields = list(fields(RESOURCE_TEMPLATE))
    resources = {
        section.removeprefix("global_resource_")
        for section, _, _ in resource_fields
        if section.startswith("global_resource_")
    }
    if resources != {"minerals", "alloys", "science", "unity", "strategic", "titanPermit", "colossusPermit"}:
        ERRORS.append(f"resource template has unexpected resources: {sorted(resources)}")
    if ("global_resource_titanPermit", "hidden", "true") not in resource_fields:
        ERRORS.append("technical titan permit must remain hidden from the resource HUD")
    if ("global_resource_colossusPermit", "hidden", "true") not in resource_fields:
        ERRORS.append("technical colossus permit must remain hidden from the resource HUD")
else:
    ERRORS.append("missing all-units.template")

for filename in ("faction_picker.ini", "starbase.ini", "_starbase_tier_common.ini"):
    path = ROOT / "units" / filename
    if ("core", "tags", "rsCapital") not in list(fields(path)):
        ERRORS.append(f"{filename}: capital unit chain must retain rsCapital tag")

for name, (path, entries) in UNITS.items():
    sections = {s for s, _, _ in entries}
    action_ids = [s.split("_", 1)[1] for s in sections if s.startswith(("action_", "hiddenAction_"))]
    if len(action_ids) != len(set(action_ids)):
        ERRORS.append(f"{path.name}: visible and hidden actions share an ID")
    inherited = [v for s, k, v in entries if s == "core" and k == "copyFrom"]
    for parent in inherited:
        if not (path.parent / parent).is_file():
            ERRORS.append(f"{path.name}: missing copyFrom {parent}")
    for required in (("core", "graphics") if inherited else ("core", "graphics", "attack", "movement")):
        if required not in sections:
            ERRORS.append(f"{path.name}: missing [{required}]")
    for section, key, value in entries:
        if section == "core" and key == "techLevel":
            try:
                if not 1 <= int(value) <= 3:
                    ERRORS.append(f"{path.name}: techLevel must be 1-3 in game 1.15")
            except ValueError:
                ERRORS.append(f"{path.name}: invalid techLevel {value}")
        if section == "graphics" and key in ("image", "image_wreak"):
            if not (path.parent / value).is_file():
                ERRORS.append(f"{path.name}: missing sprite {value}")
        if section == "core" and re.match(r"(?:canBuild|builtFrom)_\d+_name", key):
            for target in (v.strip() for v in value.split(",")):
                if target.startswith("rs") and target not in UNITS:
                    ERRORS.append(f"{path.name}: unknown unit {target}")
        if section.startswith("canBuild_") and key == "name" and value.startswith("rs") and value not in UNITS:
            ERRORS.append(f"{path.name}: unknown unit {value}")
        if (section.startswith("action_") or section.startswith("hiddenAction_")) and key == "convertTo" and value.startswith("rs") and value not in UNITS:
            ERRORS.append(f"{path.name}: unknown conversion target {value}")
        if section == "core" and key in ("price", "generation_resources") and "=" in value:
            for pair in value.split(","):
                resource = pair.split("=", 1)[0].strip()
                if resource not in resources | {"credits"}:
                    ERRORS.append(f"{path.name}: unknown resource {resource}")
        unit_energy_price = section.startswith("action_") and key == "price" and any(
            s == "core" and k == "energyMax" for s, k, _ in entries
        )
        if re.search(r"(?<![A-Za-z_])energy\s*=", value) and not unit_energy_price:
            ERRORS.append(f"{path.name}: obsolete custom energy reference in [{section}] {key}")

for name, expected in (("rsGenerator", "credits=12"), ("rsGeneratorT2", "credits=24"), ("rsGeneratorT3", "credits=48"), ("rsTradeHub", "credits=16")):
    if name in UNITS:
        path, entries = UNITS[name]
        production = [v for s, k, v in entries if s == "core" and k == "generation_resources"]
        if production != [expected]:
            ERRORS.append(f"{path.name}: expected native energy-credit production {expected}, got {production}")

if "rsFactionPicker" in UNITS:
    path, entries = UNITS["rsFactionPicker"]
    if ("core", "price", "2000") not in entries:
        ERRORS.append(f"{path.name}: expected affordable native-map entry price of 2000 credits")

if "rsEngineer" in UNITS:
    path, entries = UNITS["rsEngineer"]
    if ("core", "isBuilder", "true") not in entries:
        ERRORS.append(f"{path.name}: engineer must be marked as a builder")
    if ("ai", "useAsBuilder", "true") not in entries:
        ERRORS.append(f"{path.name}: AI must use the engineer as a builder")
    if any(s.startswith("canBuild_") and k == "name" and v == "rsPlanetLab" for s, k, v in entries):
        ERRORS.append("planet lab must upgrade from the research station")

for name in ("rsStarbase", "rsStarhold", "rsFortress", "rsCitadel"):
    if name in UNITS:
        path, entries = UNITS[name]
        common = (path.parent / "_starbase_tier_common.ini") if name != "rsStarbase" else None
        effective = entries + (list(fields(common)) if common else [])
        for key in ("autoRepair", "canRepairUnits", "nanoRange", "nanoRepairSpeed"):
            if not any(s == "core" and k == key for s, k, _ in effective):
                ERRORS.append(f"{path.name}: missing fleet repair field {key}")

if "rsResearchStation" in UNITS and "rsPlanetLab" in UNITS:
    station_actions = {s for s, _, _ in UNITS["rsResearchStation"][1] if s.startswith("action_research")}
    lab_actions = {s for s, _, _ in UNITS["rsPlanetLab"][1] if s.startswith("action_research")}
    if station_actions != lab_actions:
        ERRORS.append("planet lab must retain every research project")
    if ("action_upgradePlanetLab", "convertTo", "rsPlanetLab") not in UNITS["rsResearchStation"][1]:
        ERRORS.append("research station must upgrade to planet lab")

for name in ("rsResearchStation", "rsPlanetLab"):
    if name in UNITS and ("action_researchTitan", "addResources", "titanPermit=1") not in UNITS[name][1]:
        ERRORS.append(f"{name}: titan research must grant one build permit")
if "rsTitan" in UNITS:
    titan = UNITS["rsTitan"][1]
    if ("hiddenAction_returnTitanPermit", "autoTriggerOnEvent", "destroyed") not in titan:
        ERRORS.append("titan permit return must run on destruction")
    if ("hiddenAction_returnTitanPermit", "addResources", "titanPermit=1") not in titan:
        ERRORS.append("titan destruction must return its build permit")
    if not any(s == "core" and k == "price" and "titanPermit=1" in v for s, k, v in titan):
        ERRORS.append("titan production must consume its build permit")

if all(name in UNITS for name in ("rsScienceNexusSite", "rsScienceNexusFrame", "rsScienceNexus")):
    site = UNITS["rsScienceNexusSite"][1]
    frame = UNITS["rsScienceNexusFrame"][1]
    complete = UNITS["rsScienceNexus"][1]
    if ("action_buildScienceNexusFrame", "convertTo", "rsScienceNexusFrame") not in site:
        ERRORS.append("science nexus site must convert to frame")
    if ("action_completeScienceNexus", "convertTo", "rsScienceNexus") not in frame:
        ERRORS.append("science nexus frame must convert to complete structure")
    if any(s == "core" and k == "generation_resources" for s, k, _ in site + frame):
        ERRORS.append("unfinished science nexus must not generate science")
    if ("core", "generation_resources", "science=45") not in complete:
        ERRORS.append("completed science nexus must generate 45 science")

if all(name in UNITS for name in ("rsQuantumCatapultSite", "rsQuantumCatapultFrame", "rsQuantumCatapult")):
    site = UNITS["rsQuantumCatapultSite"][1]
    frame = UNITS["rsQuantumCatapultFrame"][1]
    complete = UNITS["rsQuantumCatapult"][1]
    if ("action_buildQuantumCatapultFrame", "convertTo", "rsQuantumCatapultFrame") not in site:
        ERRORS.append("quantum catapult site must convert to frame")
    if ("action_completeQuantumCatapult", "convertTo", "rsQuantumCatapult") not in frame:
        ERRORS.append("quantum catapult frame must convert to complete structure")
    for action, exit_tag in (("launchA", "rsQuantumExitA"), ("launchB", "rsQuantumExitB")):
        if (f"action_{action}", "takeResources_excludeUnitsWithoutTags", "rsQuantumFleet") not in complete:
            ERRORS.append(f"quantum catapult {action} must select only fleet units")
        if (f"hiddenAction_sendToExit{action[-1]}", "sendMessageWithData", f"exit=globalSearchForFirstUnit(withTag='{exit_tag}', relation='any')") not in complete:
            ERRORS.append(f"quantum catapult {action} must target its map exit")
    for name in ("rsCorvette", "rsDestroyer"):
        entries = UNITS[name][1]
        if ("core", "tags", "rsQuantumFleet") not in entries or ("hiddenAction_receiveQuantumLaunch", "teleportTo", "eventData('exit', type='unit')") not in entries:
            ERRORS.append(f"{name} must receive quantum launch messages")

for name in ("rsGenerator", "rsMiningStation", "rsResearchStation", "rsShipyard", "rsFoundry"):
    if name in UNITS and not any(s == "ai" and k == "buildPriority" and float(v) > 0 for s, k, v in UNITS[name][1]):
        ERRORS.append(f"{UNITS[name][0].name}: core AI economy needs positive build priority")
if "rsFoundry" in UNITS and ("action_smelting", "ai_isHighPriority", "true") not in UNITS["rsFoundry"][1]:
    ERRORS.append("foundry alloy conversion must be available to AI")

if not (ROOT / "mod-info.txt").is_file():
    ERRORS.append("missing mod-info.txt")

overrides = [name for name, (_, entries) in UNITS.items() if any(s == "core" and k == "overrideAndReplace" and v in {"commandCenter", "builder"} for s, k, v in entries)]
if overrides:
    ERRORS.append(f"vanilla command center and builder must remain available: {overrides}")
if "rsFactionPicker" in UNITS and ("core", "builtFrom_1_name", "builder") not in UNITS["rsFactionPicker"][1]:
    ERRORS.append("faction picker must be buildable by the vanilla builder")
if "rsEngineer" in UNITS and ("core", "builtFrom_2_name", "commandCenter") not in UNITS["rsEngineer"][1]:
    ERRORS.append("engineer must be buildable from the vanilla command center")

if ERRORS:
    print("\n".join(ERRORS), file=sys.stderr)
    raise SystemExit(1)
print(f"Validated {len(UNITS)} units and local sprite references")
