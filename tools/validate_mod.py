"""Check local unit references and sprite files before loading the game."""

from pathlib import Path
import re
from struct import unpack
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

for filename in ("pre_ftl_command.ini", "starbase.ini", "_starbase_tier_common.ini"):
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
    ERRORS.append("standalone faction picker must not be buildable")
if "rsPreFtlCommand" in UNITS:
    path, entries = UNITS["rsPreFtlCommand"]
    if ("core", "overrideAndReplace", "commandCenter") not in entries:
        ERRORS.append(f"{path.name}: must replace native command center")
    if ("core", "canBuild_1_name", "builder") not in entries:
        ERRORS.append(f"{path.name}: must retain native builder production")
    for action, target in (("action_regular", "rsStarbase"), ("action_machine", "rsStarbaseMachine"), ("action_hive", "rsStarbaseHive")):
        if (action, "convertTo", target) not in entries:
            ERRORS.append(f"{path.name}: missing {action} upgrade")
if "rsStarbaseOrigin" in UNITS and ("core", "isPickableStartingUnit", "true") not in UNITS["rsStarbaseOrigin"][1]:
    ERRORS.append("special maps need a stellar starting capital")

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
        range_value = next((v for s, k, v in entries if s == "core" and k == "nanoRange"), None)
        if range_value is None and common:
            range_value = next((v for s, k, v in fields(common) if s == "core" and k == "nanoRange"), None)
        attack_range = next((v for s, k, v in entries if s == "attack" and k == "maxAttackRange"), None)
        if attack_range is None and common:
            attack_range = next((v for s, k, v in fields(common) if s == "attack" and k == "maxAttackRange"), None)
        if range_value != attack_range:
            ERRORS.append(f"{path.name}: repair and displayed attack ranges differ")

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
    catapult = UNITS["rsQuantumCatapult"][1]
    if not any(s == "hiddenAction_aiEconomicRaid" and k == "autoTrigger" and "self.isControlledByAI" in v and "rsRaidFleet" in v and "rsEconomicTarget" in v for s, k, v in catapult):
        ERRORS.append("AI catapult raid must require AI control, an assembled advanced fleet, and an enemy economy target")
    if ("hiddenAction_sendRaidFleet", "sendMessageWithTags", "rsQuantumRaid") not in catapult:
        ERRORS.append("AI catapult raid must notify selected ships")
    if ("hiddenAction_receiveQuantumRaid", "teleportTo", "eventData('target', type='unit')") not in UNITS["rsDestroyer"][1]:
        ERRORS.append("raid fleet must teleport to the enemy economy target")
    if ("hiddenAction_raidEconomicTarget", "addWaypoint_type", "attack") not in UNITS["rsDestroyer"][1]:
        ERRORS.append("raid fleet must attack an economy target after arrival")
    for name in ("rsGenerator", "rsGeneratorT2", "rsGeneratorT3", "rsResearchStation", "rsPlanetLab", "rsFoundry", "rsTradeHub"):
        if name in UNITS and ("core", "tags", "rsEconomicTarget") not in UNITS[name][1]:
            ERRORS.append(f"{name} must be a strategic economy target")
    for name, section in (("rsQuantumCatapultSite", "action_buildQuantumCatapultFrame"), ("rsQuantumCatapultFrame", "action_completeQuantumCatapult")):
        if (section, "ai_isHighPriority", "true") not in UNITS[name][1]:
            ERRORS.append(f"{name} must be able to progress its construction under AI control")
    for name in ("rsResearchStation", "rsPlanetLab"):
        if name in UNITS and ("action_researchQuantumCatapult", "ai_isHighPriority", "if self.resource('rsAiHandicap') >= 1.8") not in UNITS[name][1]:
            ERRORS.append(f"{name} must prioritize catapult research for high-difficulty AI")

for name in ("rsGenerator", "rsMiningStation", "rsResearchStation", "rsShipyard", "rsFoundry"):
    if name in UNITS and not any(s == "ai" and k == "buildPriority" and float(v) > 0 for s, k, v in UNITS[name][1]):
        ERRORS.append(f"{UNITS[name][0].name}: core AI economy needs positive build priority")
for name, credits, minerals, alloys in (("rsFoundry", 2, 3, 2), ("rsFoundryT2", 4, 7, 5), ("rsFoundryT3", 8, 14, 10)):
    if name not in UNITS:
        ERRORS.append(f"missing foundry tier {name}")
        continue
    entries = UNITS[name][1]
    if ("core", "generation_resources", f"credits=-{credits}, minerals=-{minerals}, alloys={alloys}") not in entries:
        ERRORS.append(f"{name}: foundry must visibly generate alloys and consume inputs")
    if ("core", "generation_active", f"if self.resource('minerals') >= {minerals} and self.resource('credits') >= {credits}") not in entries:
        ERRORS.append(f"{name}: foundry must stop when inputs are insufficient")
    if name == "rsFoundry" and ("core", "generation_delay", "120") not in entries:
        ERRORS.append("foundry automatic smelting must run at the designed two-second interval")

for source, target, action in (("rsCruiser", "rsCruiserT2", "action_upgradeCruiserT2"), ("rsCruiserMissile", "rsCruiserMissileT2", "action_upgradeCruiserT2"), ("rsCarrierCruiser", "rsCarrierCruiserT2", "action_upgradeCruiserT2"), ("rsBattleship", "rsBattleshipT2", "action_upgradeBattleshipT2"), ("rsMissileBattleship", "rsMissileBattleshipT2", "action_upgradeBattleshipT2")):
    if source not in UNITS or target not in UNITS:
        ERRORS.append(f"missing T2 ship path: {source} -> {target}")
        continue
    if (action, "convertTo", target) not in UNITS[source][1]:
        ERRORS.append(f"{source}: missing T2 conversion")
    entries = UNITS[target][1]
    if not any(s == "core" and k == "maxShield" and int(v) > 0 for s, k, v in entries):
        ERRORS.append(f"{target}: missing T2 shield")
    if not any(s == "core" and k == "selfRegenRate" and float(v) > 0 for s, k, v in entries):
        ERRORS.append(f"{target}: missing T2 hull repair")
    if "Battleship" in target and not any(s == "turret_laserDefence" and k == "laserDefenceEnergyUse" for s, k, v in entries):
        ERRORS.append(f"{target}: missing visible native laser defence")
for name, action in (("rsCruiser", "action_upgradeCruiserT2"), ("rsBattleship", "action_upgradeBattleshipT2")):
    if (action, "isLocked", "if not self.globalTeamTags(includes='rsTechShields')") not in UNITS[name][1]:
        ERRORS.append(f"{name}: T2 upgrade must require shield research")
for name, action in (("rsBattleship", "action_upgradeCruiserT2"), ("rsTitan", "action_upgradeBattleshipT2"), ("rsJuggernaut", "action_upgradeBattleshipT2")):
    if (action, "isVisible", "false") not in UNITS[name][1]:
        ERRORS.append(f"{name}: inherited lower-hull upgrade must be hidden")
if "rsJuggernaut" in UNITS:
    entries = UNITS["rsJuggernaut"][1]
    for target in ("rsCruiserT2", "rsCruiserMissileT2", "rsCarrierCruiserT2", "rsBattleshipT2", "rsMissileBattleshipT2"):
        if not any(s.startswith("canBuild_") and k == "name" and v == target for s, k, v in entries):
            ERRORS.append(f"rsJuggernaut: missing direct T2 build {target}")
for name, expected in (("rsCorvette", "1.65"), ("rsDestroyer", "1.55"), ("rsCruiser", "1.45"), ("rsCarrierCruiser", "1.4"), ("rsBattleship", "1.3")):
    if ("movement", "moveSpeed", expected) not in UNITS[name][1]:
        ERRORS.append(f"{name}: mixed-fleet speed should be {expected}")

for name, credits, expected in (("rsMiningStation", 8, 4), ("rsMiningStationBoosted", 8, 6), ("rsMiningStationT2", 12, 8), ("rsMiningStationT2Boosted", 12, 12), ("rsMiningStationT3", 16, 16), ("rsMiningStationT3Boosted", 16, 24)):
    if name not in UNITS:
        ERRORS.append(f"missing mining tier {name}")
    elif ("core", "generation_resources", f"credits={credits}, minerals={expected}") not in UNITS[name][1]:
        ERRORS.append(f"{name}: expected credits={credits}, minerals={expected}")
if "rsCruiserMissile" in UNITS:
    entries = UNITS["rsCruiserMissile"][1]
    for expected in (("turret_2", "projectile", "1"), ("projectile_1", "directDamage", "170"), ("projectile_1", "targetSpeed", "7")):
        if expected not in entries:
            ERRORS.append(f"missile cruiser must retain its dual fast-missile salvo: {expected}")
for name, life, resistance in (("rsCruiserMissile", "300", "6"), ("rsMissileBattleship", "360", "10")):
    if name in UNITS:
        entries = UNITS[name][1]
        for expected in (("projectile_1", "life", life), ("projectile_1", "deflectionPower", resistance), ("projectile_1", "autoTargetingOnDeadTarget", "true")):
            if expected not in entries:
                ERRORS.append(f"{name}: heavy missile flight or interception behavior regressed: {expected}")
if "rsMineralPlant" in UNITS:
    entries = UNITS["rsMineralPlant"][1]
    if ("core", "tags", "rsMineralPlant") not in entries or any(s == "core" and k == "generation_resources" for s, k, _ in entries):
        ERRORS.append("mineral plant must boost stations without directly producing minerals")
if "rsEngineer" in UNITS and not any(
    s == "canBuild_mineralPlant" and k == "isLocked" and "incompleteBuildings=true" in v
    for s, k, v in UNITS["rsEngineer"][1]
):
    ERRORS.append("mineral plant cap must count unfinished construction")

if not (ROOT / "mod-info.txt").is_file():
    ERRORS.append("missing mod-info.txt")

overrides = {(name, v) for name, (_, entries) in UNITS.items() for s, k, v in entries if s == "core" and k == "overrideAndReplace"}
if overrides != {("rsPreFtlCommand", "commandCenter"), ("rsPreFtlBuilder", "builder"), ("rsPreFtlMine", "extractor"), ("rsNativeGunT3Bridge", "c_turret_t3_gun"), ("rsNativeSamT3Bridge", "c_antiAirTurretT3")}:
    ERRORS.append(f"native replacements must include capital, builder, extractor, and T3 towers: {overrides}")
for tier, target, minerals in (
    ("rsMiningStationT3", "rsDeepMiningStation", 16),
    ("rsMiningStationT3Boosted", "rsDeepMiningStationBoosted", 24),
):
    if tier in UNITS and target in UNITS:
        upgrade = UNITS[tier][1]
        deep = UNITS[target][1]
        if ("action_upgradeDeepMining", "convertTo", target) not in upgrade:
            ERRORS.append(f"{tier} must upgrade to {target}")
        if not any(section == "action_upgradeDeepMining" and key == "isLocked" and "rsTechCruiser" in value and "rsRareDeposit" not in value for section, key, value in upgrade):
            ERRORS.append(f"{tier} must require cruiser technology and allow ordinary deposits on every map")
        if ("core", "generation_resources", f"credits=16, minerals={minerals}, strategic=0.25") not in deep:
            ERRORS.append(f"{target} must preserve mining and add a small strategic byproduct")
if "rsDeepMiningStation" in UNITS and ("hiddenAction_applyProcessingBonus", "convertTo", "rsDeepMiningStationBoosted") not in UNITS["rsDeepMiningStation"][1]:
    ERRORS.append("deep mining station must react to mineral processing")
if "rsDeepMiningStationBoosted" in UNITS and ("hiddenAction_removeProcessingBonus", "convertTo", "rsDeepMiningStation") not in UNITS["rsDeepMiningStationBoosted"][1]:
    ERRORS.append("boosted deep mining station must revert after processing ends")
for platform, bridge, action, tech in (
    ("rsDefensePlatform", "rsNativeGunT3Bridge", "action_upgradeDefensePlatform", "rsTechDestroyer"),
    ("rsMissilePlatform", "rsNativeSamT3Bridge", "action_upgradeMissilePlatform", "rsTechMissiles"),
):
    if platform in UNITS and bridge in UNITS:
        platform_entries = UNITS[platform][1]
        bridge_entries = UNITS[bridge][1]
        if platform == "rsDefensePlatform" and ("core", "selfRegenRate", "0.10") not in platform_entries:
            ERRORS.append("defense platform must retain T3 gun turret self repair")
        for key in ("footprint", "constructionFootprint"):
            if ("core", key, "0,0,0,1") not in platform_entries:
                ERRORS.append(f"{platform} must occupy 1x2")
        if ("core", "displayFootprint", "0,0,1,1") not in platform_entries:
            ERRORS.append(f"{platform} selection frame must match native 2x2 towers")
        if not any(section == "graphics" and key == "image_turret" for section, key, _ in platform_entries):
            ERRORS.append(f"{platform} must have a rotating turret sprite")
        if (action, "convertTo", platform) not in bridge_entries or not any(section == action and key == "isLocked" and tech in value for section, key, value in bridge_entries):
            ERRORS.append(f"{bridge} must upgrade to {platform} after {tech}")
if "rsPreFtlCommand" in UNITS:
    entries = UNITS["rsPreFtlCommand"][1]
    if any(s == "core" and k.startswith("canBuild_") and v == "rsEngineer" for s, k, v in entries):
        ERRORS.append("command center must not produce engineers")
    if ("action_researchFTL", "addGlobalTeamTags", "rsTechFTL") not in entries:
        ERRORS.append("command center must research FTL before upgrading")
    for faction in ("regular", "machine", "hive"):
        if (f"action_{faction}", "price", "credits=5000, minerals=150") not in entries:
            ERRORS.append(f"{faction} empire must pay the new entry cost")
if "rsPreFtlBuilder" in UNITS:
    entries = UNITS["rsPreFtlBuilder"][1]
    if ("action_upgradeEngineer", "convertTo", "rsEngineer") not in entries:
        ERRORS.append("native builder must convert into an engineer")
    if ("core", "canBuild_1_name", "extractor") not in entries:
        ERRORS.append("pre-FTL builder must retain the native extractor menu entry")
if "rsPreFtlMine" not in UNITS:
    ERRORS.append("missing pre-FTL extractor replacement")
else:
    entries = UNITS["rsPreFtlMine"][1]
    if ("core", "generation_resources", "credits=8, minerals=2") not in entries or ("action_upgradeMining", "convertTo", "rsMiningStation") not in entries:
        ERRORS.append("pre-FTL extractor must generate credits and minerals and upgrade into a mining station")
if "rsEngineer" in UNITS and any(s == "core" and k.startswith("builtFrom_") and v == "commandCenter" for s, k, v in UNITS["rsEngineer"][1]):
    ERRORS.append("engineer must only be produced at a starbase or above")
for sprite_name, world_size in (
    ("starbase", 64), ("starhold", 96), ("fortress", 96), ("citadel", 96),
    ("outpost", 48), ("engineer", 32), ("science_ship", 40),
    ("corvette", 32), ("destroyer", 48), ("cruiser", 64),
    ("battleship", 80), ("generator", 48), ("mining_station", 48),
    ("research_station", 48), ("shipyard", 64),
):
    path = ROOT / "units" / f"{sprite_name}.png"
    ini = ROOT / "units" / f"{sprite_name}.ini"
    if not path.is_file() or not ini.is_file():
        ERRORS.append(f"missing high-resolution sprite or unit config for {sprite_name}")
        continue
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or not 3 * world_size <= min(unpack(">II", data[16:24])) <= 384:
        ERRORS.append(f"{sprite_name}: playable sprite must retain zoom detail within the texture budget")
    if ("graphics", "scaleImagesTo", str(world_size)) not in list(fields(ini)):
        ERRORS.append(f"{sprite_name}: world size must remain {world_size}")
for source in (ROOT.parent.parent / "art" / "generated").glob("*-source.png"):
    name = source.name.removesuffix("-source.png")
    sprite = ROOT / "units" / f"{name}.png"
    ini = ROOT / "units" / f"{name}.ini"
    if not sprite.is_file() or not ini.is_file():
        continue
    data = sprite.read_bytes()[:24]
    scale = next((int(v) for s, k, v in fields(ini) if s == "graphics" and k == "scaleImagesTo"), None)
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or scale is None or not 3 * scale <= min(unpack(">II", data[16:24])) <= 384:
        ERRORS.append(f"{name}: generated playable sprite must keep zoom detail within the texture budget")
    if scale is None:
        ERRORS.append(f"{name}: source sprite requires a fixed world size")
for sprite in (ROOT / "units").glob("*.png"):
    data = sprite.read_bytes()[:24]
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and max(unpack(">II", data[16:24])) > 384:
        ERRORS.append(f"{sprite.name}: game sprite exceeds 384px texture budget")
for name in ("rsTitan", "rsJuggernaut"):
    if name in UNITS and ("core", "experimental", "true") not in UNITS[name][1]:
        ERRORS.append(f"{name}: fourth-era capital ship must use the native experimental AI category")

if ERRORS:
    print("\n".join(ERRORS), file=sys.stderr)
    raise SystemExit(1)
print(f"Validated {len(UNITS)} units and local sprite references")
