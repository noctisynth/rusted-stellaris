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
    if resources != {"minerals", "alloys", "science", "unity", "strategic", "titanPermit", "juggernautPermit", "colossusPermit"}:
        ERRORS.append(f"resource template has unexpected resources: {sorted(resources)}")
    if ("global_resource_titanPermit", "hidden", "true") not in resource_fields:
        ERRORS.append("technical titan permit must remain hidden from the resource HUD")
    if ("global_resource_juggernautPermit", "hidden", "true") not in resource_fields:
        ERRORS.append("technical juggernaut permit must remain hidden from the resource HUD")
    if ("global_resource_colossusPermit", "hidden", "true") not in resource_fields:
        ERRORS.append("technical colossus permit must remain hidden from the resource HUD")
    for label, minimum, maximum, amounts in (
        ("Hard", "1.4", "1.8", ("minerals=2", "alloys=1", "science=4", "strategic=0.2")),
        ("VeryHard", "1.8", "3.7", ("minerals=5", "alloys=3", "science=10", "strategic=0.5")),
        ("Impossible", "3.7", None, ("minerals=10", "alloys=6", "science=20", "strategic=1")),
    ):
        section = f"hiddenAction_aiEconomy{label}"
        trigger = next((v for s, k, v in resource_fields if s == section and k == "autoTrigger"), "")
        grant = next((v for s, k, v in resource_fields if s == section and k == "addResourcesWithLogic"), "")
        if f"rsAiHandicap') >= {minimum}" not in trigger or "self.customTimer > 10" not in trigger or (maximum and f"rsAiHandicap') < {maximum}" not in trigger):
            ERRORS.append(f"{label} AI economy bonus must use its difficulty and timer gate")
        if any(amount not in grant for amount in amounts) or "self.numberOfUnitsInTeam(withTag='rsCapital')" not in grant or (section, "resetCustomTimer", "true") not in resource_fields:
            ERRORS.append(f"{label} AI economy bonus must distribute all four resources once per team")
else:
    ERRORS.append("missing all-units.template")

for filename in ("pre_ftl_command.ini", "starbase.ini", "_starbase_tier_common.ini"):
    path = ROOT / "units" / filename
    if ("core", "tags", "rsCapital") not in list(fields(path)):
        ERRORS.append(f"{filename}: capital unit chain must retain rsCapital tag")
for filename in ("pre_ftl_command.ini", "starbase.ini", "_starbase_tier_common.ini", "outpost.ini"):
    if ("core", "autoTriggerCooldownTime", "2s") not in list(fields(ROOT / "units" / filename)):
        ERRORS.append(f"{filename}: capital economy actions need a bounded trigger rate")

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
        unit_energy_price = (section.startswith("action_") or section.startswith("hiddenAction_")) and key == "price" and any(
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
    if ("action_upgradeArk", "convertTo", "rsArk") not in entries or not any(
        s == "action_upgradeArk" and k == "isLocked" and "rsTechShields" in v for s, k, v in entries
    ):
        ERRORS.append("engineer must upgrade to ark after shield research")

if "rsArk" in UNITS:
    path, entries = UNITS["rsArk"]
    if ("core", "copyFrom", "engineer.ini") not in entries:
        ERRORS.append(f"{path.name}: must inherit the engineer build menu")
    for expected in (("core", "maxHp", "2500"), ("core", "maxShield", "2200"), ("core", "selfRegenRate", "0.25"), ("core", "autoRepair", "true"), ("core", "canRepairUnits", "true"), ("core", "nanoRepairSpeed", "0.80"), ("core", "canBuild_5_name", "rsOutpost"), ("attack", "canAttackFlyingUnits", "true")):
        if expected not in entries:
            ERRORS.append(f"{path.name}: missing ark capability {expected}")
if "rsEngineer" in UNITS and ("core", "canBuild_5_name", "rsOutpost") in UNITS["rsEngineer"][1]:
    ERRORS.append("ordinary engineer must not build a stellar outpost")

if "rsOutpost" in UNITS:
    path, entries = UNITS["rsOutpost"]
    for expected in (("core", "tags", "rsCapital"), ("core", "autoRepair", "true"), ("core", "canRepairUnits", "true"), ("core", "maxHp", "4500"), ("core", "builtFrom_1_name", "rsArk"), ("action_upgradeRegular", "convertTo", "rsStarbase"), ("action_upgradeMachine", "convertTo", "rsStarbaseMachine"), ("action_upgradeHive", "convertTo", "rsStarbaseHive")):
        if expected not in entries:
            ERRORS.append(f"{path.name}: missing frontier support capability {expected}")

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
    if name in UNITS and not any(s == "action_researchDestroyer" and k == "isLocked" and "rsFactionRegular" in v and "rsFactionMachine" in v and "rsFactionHive" in v for s, k, v in UNITS[name][1]):
        ERRORS.append(f"{name}: pre-FTL science must not bypass empire selection")
if "rsTitan" in UNITS:
    titan = UNITS["rsTitan"][1]
    if ("hiddenAction_returnTitanPermit", "autoTriggerOnEvent", "destroyed") not in titan:
        ERRORS.append("titan permit return must run on destruction")
    if ("hiddenAction_returnTitanPermit", "addResources", "titanPermit=1") not in titan:
        ERRORS.append("titan destruction must return its build permit")
    if not any(s == "core" and k == "price" and "titanPermit=1" in v for s, k, v in titan):
        ERRORS.append("titan production must consume its build permit")
for name in ("rsResearchStation", "rsPlanetLab"):
    if name in UNITS and ("action_researchJuggernaut", "addResources", "juggernautPermit=1") not in UNITS[name][1]:
        ERRORS.append(f"{name}: juggernaut research must grant one build permit")
if "rsJuggernaut" in UNITS:
    juggernaut = UNITS["rsJuggernaut"][1]
    for entry in (("core", "tags", "rsQuantumFleet, rsRaidFleet, rsJuggernaut"), ("core", "nanoFactorySpeed", "2"), ("hiddenAction_returnJuggernautPermit", "autoTriggerOnEvent", "destroyed"), ("hiddenAction_returnJuggernautPermit", "addResources", "juggernautPermit=1")):
        if entry not in juggernaut:
            ERRORS.append(f"juggernaut missing limit contract {entry}")
    if not any(s == "core" and k == "price" and "juggernautPermit=1" in v for s, k, v in juggernaut):
        ERRORS.append("juggernaut production must consume its build permit")
for name, upgrade_target in (("rsTitan", "rsParadoxTitan"),):
    if name in UNITS:
        entries = UNITS[name][1]
        if ("action_upgradeParadoxTitan", "convertTo", upgrade_target) not in entries:
            ERRORS.append(f"{name} must retain its paradox upgrade target")
if "rsTitan" in UNITS:
    titan_entries = UNITS["rsTitan"][1]
    for expected in (("attack", "turretMultiTargeting", "true"), ("attack", "shootDelay", "115"), ("turret_2", "canAttackLandUnits", "false"), ("turret_2", "delay", "13"), ("turret_3", "copyFrom", "2"), ("turret_4", "projectile", "4"), ("turret_4", "limitingRange", "405"), ("projectile_1", "directDamage", "2100"), ("projectile_3", "directDamage", "110"), ("projectile_4", "tags", "rsMissile"), ("projectile_4", "instant", "false"), ("projectile_4", "deflectionPower", "3")):
        if expected not in titan_entries:
            ERRORS.append(f"titan anti-air battery missing {expected}")
for capital_name in ("rsCruiser", "rsBattleship", "rsTitan"):
    if capital_name in UNITS and ("projectile_1", "instant", "true") not in UNITS[capital_name][1]:
        ERRORS.append(f"{capital_name} main energy weapon must bypass projectile interception")
if "rsCruiser" in UNITS and ("turret_pd", "@copyFrom_skipThisSection", "true") not in UNITS["rsCruiser"][1]:
    ERRORS.append("capital ships must not inherit destroyer point defense")
for missile_name in ("rsCruiserMissile", "rsMissileBattleship"):
    if missile_name in UNITS and ("projectile_1", "instant", "false") not in UNITS[missile_name][1]:
        ERRORS.append(f"{missile_name} must retain visible guided missiles")
if "rsColossus" in UNITS:
    colossus_entries = UNITS["rsColossus"][1]
    if ("attack", "maxAttackRange", "900") not in colossus_entries:
        ERRORS.append("colossus strike distance must be at least doubled")
    for number in range(1, 6):
        if (f"projectile_{number}", "deflectionPower", "-1") not in colossus_entries:
            ERRORS.append(f"colossus weapon {number} must resist point defense")
    for queue_section, queued_action, target_tag in (
        ("hiddenAction_aiQueueNeutronSweep", "aiNeutronSweep", "rsPlanetColony"),
        ("hiddenAction_aiQueueWorldCrackerEconomic", "aiWorldCrackerEconomic", "rsEconomicTarget"),
        ("hiddenAction_aiQueueWorldCrackerCapital", "aiWorldCrackerCapital", "rsCapital"),
    ):
        trigger = next((v for s, k, v in colossus_entries if s == queue_section and k == "autoTrigger"), "")
        if "self.isControlledByAI" not in trigger or target_tag not in trigger or "queueSize(withActionTag='rsAiColossusStrike')==0" not in trigger:
            ERRORS.append(f"AI Colossus queue gate missing for {queued_action}")
        if (queue_section, "alsoQueueAction", queued_action) not in colossus_entries:
            ERRORS.append(f"AI Colossus must queue {queued_action} so charging is respected")
        action_section = f"action_{queued_action}"
        for expected in ((action_section, "tags", "rsAiColossusStrike"), (action_section, "buildSpeed", "45s")):
            if expected not in colossus_entries:
                ERRORS.append(f"AI Colossus charged strike missing {expected}")
    if not any(s == "ai" and k == "buildPriority" for s, k, _ in colossus_entries):
        ERRORS.append("AI must have a production priority for the Colossus")
    if not any(s == "hiddenAction_announceCompletion" and k == "showMessageToAllEnemyPlayers" for s, k, _ in colossus_entries):
        ERRORS.append("Colossus completion must give opponents the observer notice")
    if any(s == "hiddenAction_announceCompletion" and k == "showMessageToAllPlayers" for s, k, _ in colossus_entries):
        ERRORS.append("Colossus builder must not receive both completion viewpoints")
    for phrase in ("地壳已经破裂", "中子羽流正逐渐散去", "整个世界归于沉寂"):
        if not any(phrase in value for _, _, value in UNITS["rsColossus"][1] + sum((entries for name, (_, entries) in UNITS.items() if name.startswith("rsPlanet")), [])):
            ERRORS.append(f"Stellaris-style Colossus notice missing phrase: {phrase}")

for milestone_name in ("rsTitan", "rsParadoxTitan", "rsJuggernaut", "rsDysonSphere", "rsMatterDecompressor", "rsMegaShipyard", "rsScienceNexus", "rsQuantumCatapult"):
    if milestone_name in UNITS:
        milestone_entries = UNITS[milestone_name][1]
        if any(s == "hiddenAction_announceCompletion" and k == "showMessageToPlayer" for s, k, _ in milestone_entries):
            if not any(s == "hiddenAction_announceCompletion" and k == "showMessageToAllEnemyPlayers" for s, k, _ in milestone_entries):
                ERRORS.append(f"{milestone_name} must separate builder and opponent completion notices")
            if any(s == "hiddenAction_announceCompletion" and k == "showMessageToAllPlayers" for s, k, _ in milestone_entries):
                ERRORS.append(f"{milestone_name} builder must not receive both completion viewpoints")
if "rsParadoxTitan" in UNITS:
    paradox_entries = UNITS["rsParadoxTitan"][1]
    for expected in (("core", "maxShield", "20000"), ("core", "shieldRegen", "0.70"), ("core", "selfRegenRate", "0.25"), ("attack", "shootDelay", "90"), ("turret_2", "limitingRange", "300"), ("turret_2", "delay", "10"), ("turret_3", "limitingRange", "300"), ("turret_3", "delay", "10"), ("turret_laserDefence", "laserDefenceEnergyUse", "0.16"), ("projectile_1", "directDamage", "4800"), ("projectile_3", "directDamage", "200")):
        if expected not in paradox_entries:
            ERRORS.append(f"paradox titan missing {expected}")
for name, section, key, value in (("rsPreFtlBuilder", "core", "canBuild_16_name", "rsGenerator"), ("rsPreFtlBuilder", "core", "canBuild_17_name", "rsResearchStation"), ("rsArk", "canBuild_planetDefense", "name", "rsDefensePlatform"), ("rsArk", "canBuild_planetMissile", "name", "rsMissilePlatform"), ("rsArk", "canBuild_repairBaseDirect", "name", "rsRepairBase")):
    if name in UNITS and (section, key, value) not in UNITS[name][1]:
        ERRORS.append(f"{name} construction menu missing {value}")
if "rsMegaShipyard" in UNITS:
    mega_shipyard = UNITS["rsMegaShipyard"][1]
    if ("core", "nanoFactorySpeed", "4") not in mega_shipyard:
        ERRORS.append("mega shipyard must build at quadruple factory speed")
    for section, unit_name in (
        ("canBuild_cruiserT2", "rsCruiserT2"),
        ("canBuild_cruiserMissileT2", "rsCruiserMissileT2"),
        ("canBuild_carrierCruiserT2", "rsCarrierCruiserT2"),
        ("canBuild_battleshipT2", "rsBattleshipT2"),
        ("canBuild_missileBattleshipT2", "rsMissileBattleshipT2"),
    ):
        if (section, "name", unit_name) not in mega_shipyard:
            ERRORS.append(f"mega shipyard must directly build {unit_name}")
for name, build_speed in (
    ("rsCruiser", "0.00082"),
    ("rsCarrierCruiser", "0.00067"),
    ("rsBattleship", "0.00052"),
    ("rsTitan", "0.00026"),
    ("rsJuggernaut", "0.00021"),
    ("rsColossus", "0.00019"),
):
    if name in UNITS and ("core", "buildSpeed", build_speed) not in UNITS[name][1]:
        ERRORS.append(f"{name}: capital ship construction baseline must be {build_speed}")
for site, frame, first_action, final_action in (
    ("rsDysonSite", "rsDysonFrame", "action_buildDysonFrame", "action_completeDyson"),
    ("rsMatterSite", "rsMatterFrame", "action_buildMatterFrame", "action_completeMatter"),
    ("rsMegaShipyardSite", "rsMegaShipyardFrame", "action_buildMegaShipyardFrame", "action_completeMegaShipyard"),
    ("rsScienceNexusSite", "rsScienceNexusFrame", "action_buildScienceNexusFrame", "action_completeScienceNexus"),
    ("rsQuantumCatapultSite", "rsQuantumCatapultFrame", "action_buildQuantumCatapultFrame", "action_completeQuantumCatapult"),
):
    if site in UNITS and frame in UNITS:
        site_entries, frame_entries = UNITS[site][1], UNITS[frame][1]
        if not any(s == "ai" and k == "buildPriority" for s, k, _ in site_entries):
            ERRORS.append(f"{site} needs AI construction priority")
        if (first_action, "ai_isHighPriority", "true") not in site_entries or (final_action, "ai_isHighPriority", "true") not in frame_entries:
            ERRORS.append(f"{site} AI must complete both megastructure stages")
if "rsStrategicExtractor" in UNITS and not any(s == "ai" and k == "buildPriority" for s, k, _ in UNITS["rsStrategicExtractor"][1]):
    ERRORS.append("AI must prioritize strategic extraction before megastructure spending")
if "rsColossus" in UNITS:
    colossus = UNITS["rsColossus"][1]
    for required in (
        ("action_neutronGround", "fireTurretXAtGround", "5"),
        ("projectile_5", "buildingDamageMultiplier", "0"),
        ("projectile_5", "spawnUnit", "rsNeutronPulse"),
    ):
        if required not in colossus:
            ERRORS.append(f"ordinary-map Neutron Sweep missing {required}")
    if not any(s == "action_neutronGround" and k == "isVisible" and "rsRareDeposit" in v and "== null" in v for s, k, v in colossus):
        ERRORS.append("ordinary-map Neutron Sweep must be hidden on dedicated planet maps")
if "rsNeutronPulse" in UNITS:
    neutron_pulse = UNITS["rsNeutronPulse"][1]
    if ("core", "createNeutral", "true") not in neutron_pulse or ("projectile_1", "convertHitToSourceTeam", "true") not in neutron_pulse:
        ERRORS.append("Neutron Sweep pulse must neutralize surviving buildings")
for name in ("rsResearchStation", "rsPlanetLab"):
    if name in UNITS:
        research_prices = {s: v for s, k, v in UNITS[name][1] if s.startswith("action_research") and k == "price"}
        research_science_costs = {
            "Destroyer": 600, "Cruiser": 2500, "Kinetics": 900, "Missiles": 3000,
            "Battleship": 5500, "Carrier": 3600, "Starhold": 1400, "Fortress": 4000,
            "Citadel": 8000, "Shields": 1800, "IonCannon": 6500, "Titan": 13000,
            "Juggernaut": 16000, "Colossus": 22000,
            "ColossusMachine": 22000, "ColossusHive": 22000, "Dyson": 14000,
            "Matter": 15000, "MegaShipyard": 16000, "ScienceNexus": 15000,
            "QuantumCatapult": 18000, "HyperRelay": 2400, "TianjiEngineering": 9000,
        }
        if len(research_prices) != len(research_science_costs) or any(
            not research_prices.get(f"action_research{action}", "").startswith(f"science={cost},")
            for action, cost in research_science_costs.items()
        ):
            ERRORS.append(f"{name}: research reprice incomplete")

if all(name in UNITS for name in ("rsScienceNexusSite", "rsScienceNexusFrame", "rsScienceNexus")):
    site = UNITS["rsScienceNexusSite"][1]
    frame = UNITS["rsScienceNexusFrame"][1]
    complete = UNITS["rsScienceNexus"][1]
    if ("action_buildScienceNexusFrame", "convertTo", "rsScienceNexusFrame") not in site:
        ERRORS.append("science nexus site must convert to frame")
    if ("action_completeScienceNexus", "convertTo", "rsScienceNexus") not in frame:
        ERRORS.append("science nexus frame must convert to complete structure")
    if ("action_completeScienceNexus", "addGlobalTeamTags", "rsScienceNexusCompleted") not in frame:
        ERRORS.append("science nexus completion must permanently unlock dependent research")
    if any(s == "core" and k == "generation_resources" for s, k, _ in site + frame):
        ERRORS.append("unfinished science nexus must not generate science")
    if ("core", "generation_resources", "science=45") not in complete:
        ERRORS.append("completed science nexus must generate 45 science")
    if ("core", "tags", "rsScienceNexusChain, rsScienceNexusOnline") not in complete:
        ERRORS.append("completed science nexus must satisfy sandbox research prerequisites")

for name in ("rsResearchStation", "rsPlanetLab"):
    if name in UNITS:
        catapult_lock = next((v for s, k, v in UNITS[name][1] if s == "action_researchQuantumCatapult" and k == "isLocked"), "")
        if "rsScienceNexusCompleted" not in catapult_lock or "rsScienceNexusOnline" not in catapult_lock:
            ERRORS.append(f"{name}: quantum catapult research must require a completed science nexus")

# Training is reversible and only provided by an active academy.
for name, (_, entries) in UNITS.items():
    training = [(k, v) for section, k, v in entries if section == "hiddenAction_academyTraining"]
    if "Veteran" in name:
        ERRORS.append(f"{name}: obsolete veteran identities must be removed")
    if not training:
        continue
    values = dict(training)
    if "convertTo" in values or "setUnitStats" not in values:
        ERRORS.append(f"{name}: academy training must apply stats without changing unit identity")
    trigger = values.get("autoTrigger", "")
    if not all(part in trigger for part in ("rsConstructionComplete", "rsFleetAcademyActive", "relation='own'", "!= null", "self.hasFlag(id=1)", "self.maxHp!=")):
        ERRORS.append(f"{name}: training must gate completion, persistence and upgrade reapplication")
    if values.get("addResources") != "setFlag=1":
        ERRORS.append(f"{name}: training must persist its reserved unit flag")
    stats = values.get("setUnitStats", "")
    if "hp=self.hp*" not in stats or "/self.maxHp" not in stats or "shootDamageMultiplier=1.1" not in stats:
        ERRORS.append(f"{name}: training must preserve HP ratio and apply the agreed damage bonus")

    revoke = {k: v for section, k, v in entries if section == "hiddenAction_revokeAcademyTraining"}
    if not all(part in revoke.get("autoTrigger", "") for part in ("self.hasFlag(id=1)", "rsFleetAcademyActive", "relation='own'", "== null")):
        ERRORS.append(f"{name}: academy loss must revoke training")
    if revoke.get("addResources") != "unsetFlag=1" or "shootDamageMultiplier=1" not in revoke.get("setUnitStats", "") or "/self.maxHp" not in revoke.get("setUnitStats", ""):
        ERRORS.append(f"{name}: revocation must restore damage and preserve HP ratio")

academy = UNITS["rsFleetAcademy"][1]
for entry in (("core", "tags", "rsFleetAcademy"), ("action_trainFleet", "temporarilyAddTags", "rsFleetAcademyActive"), ("action_trainFleet", "allowMultipleInQueue", "false"), ("ai", "maxGlobal", "1")):
    if entry not in academy:
        ERRORS.append(f"academy missing facility lifecycle contract {entry}")
if any(k == "addGlobalTeamTags" and "rsAcademyTraining" in v for _, k, v in academy):
    ERRORS.append("academy training must not be a permanent team upgrade")
academy_lock = next(v for sec, k, v in UNITS["rsEngineer"][1] if sec == "canBuild_fleetAcademy" and k == "isLocked")
if "rsFleetAcademy" not in academy_lock or "incompleteBuildings=true" not in academy_lock:
    ERRORS.append("academy build limit must include unfinished buildings")

for name in ("rsCorvette", "rsDestroyer"):
    if name in UNITS:
        training_trigger = next((v for s, k, v in UNITS[name][1] if s == "hiddenAction_academyTraining" and k == "autoTrigger"), "")
        if "rsConstructionComplete" not in training_trigger:
            ERRORS.append(f"{name}: academy training must wait for ship completion")
        if ("hiddenAction_markConstructionComplete", "autoTriggerOnEvent", "completeAndActive") not in UNITS[name][1] or ("hiddenAction_markConstructionComplete", "temporarilyAddTags", "rsConstructionComplete") not in UNITS[name][1]:
            ERRORS.append(f"{name}: completion event must mark the ship before academy training")

for name, action in (("rsCruiser", "action_upgradeCruiserT2"), ("rsBattleship", "action_upgradeBattleshipT2"), ("rsTitan", "action_upgradeParadoxTitan")):
    entries = UNITS[name][1]
    if (action, "convertTo_keepCurrentTags", "true") not in entries:
        ERRORS.append(f"{name}: upgrade must preserve completion and training tags")
    if name != "rsTitan" and (action, "temporarilyAddTags", "rsTier2") not in entries:
        ERRORS.append(f"{name}: upgraded ship must gain its target tier tag")

if all(name in UNITS for name in ("rsQuantumCatapultSite", "rsQuantumCatapultFrame", "rsQuantumCatapult")):
    site = UNITS["rsQuantumCatapultSite"][1]
    frame = UNITS["rsQuantumCatapultFrame"][1]
    complete = UNITS["rsQuantumCatapult"][1]
    if ("action_buildQuantumCatapultFrame", "convertTo", "rsQuantumCatapultFrame") not in site:
        ERRORS.append("quantum catapult site must convert to frame")
    if ("action_completeQuantumCatapult", "convertTo", "rsQuantumCatapult") not in frame:
        ERRORS.append("quantum catapult frame must convert to complete structure")
    if ("core", "tags", "rsQuantumCatapultChain, rsQuantumCatapultOnline") not in complete:
        ERRORS.append("completed catapult must unlock its team's capital-ship jump")
    if any(s in ("action_launchA", "action_launchB") for s, _, _ in complete):
        ERRORS.append("catapult must not retain fixed-exit launch actions")
    engineer = UNITS["rsEngineer"][1]
    build_lock = next((v for s, k, v in engineer if s == "canBuild_quantumCatapultSite" and k == "isLocked"), "")
    if not build_lock or "rsQuantumExit" in build_lock:
        ERRORS.append("ordinary maps must permit catapult construction without fixed exits")
    cruiser = UNITS["rsCruiser"][1]
    for expected in (("action_quantumJump", "fireTurretXAtGround", "quantumJump"), ("action_quantumJump", "buildSpeed", "20s"), ("action_quantumJump", "addActionCooldownTime", "150s"), ("projectile_quantumJump", "teleportSource", "true"), ("turret_quantumJump", "limitingRange", "20000")):
        if expected not in cruiser:
            ERRORS.append(f"capital ships need a charged long-range jump: {expected}")
    jump_lock = next((v for s, k, v in cruiser if s == "action_quantumJump" and k == "isLocked"), "")
    if "rsQuantumCatapultOnline" not in jump_lock:
        ERRORS.append("capital-ship jump must require a completed team catapult")
    jump_visibility = next((v for s, k, v in cruiser if s == "action_quantumJump" and k == "isVisible"), "")
    if "rsTechQuantumCatapult" not in jump_visibility or "rsQuantumCatapultOnline" not in jump_visibility:
        ERRORS.append("sandbox-built catapult must reveal capital-ship jump without research")
    for name in ("rsCorvette", "rsDestroyer"):
        if any(s == "action_quantumJump" for s, _, _ in UNITS[name][1]):
            ERRORS.append(f"{name} must not have a capital-ship jump")
    for name, cost in (("rsBattleship", "credits=1800, strategic=2"), ("rsTitan", "credits=3000, strategic=3"), ("rsJuggernaut", "credits=3200, strategic=3")):
        if ("action_quantumJump", "price", cost) not in UNITS[name][1]:
            ERRORS.append(f"{name} must pay its capital-ship jump cost")
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
    if name == "rsFoundry" and ("core", "generation_delay", "80") not in entries:
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
for name, expected in (("rsCorvette", "1.65"), ("rsDestroyer", "1.55"), ("rsCruiser", "1.45"), ("rsCruiserMissile", "1.45"), ("rsCarrierCruiser", "1.45"), ("rsBattleship", "1.4"), ("rsTitan", "1.32"), ("rsJuggernaut", "1.27")):
    if ("movement", "moveSpeed", expected) not in UNITS[name][1]:
        ERRORS.append(f"{name}: mixed-fleet speed should be {expected}")

for name, credits, expected in (("rsMiningStation", 8, 4), ("rsMiningStationBoosted", 8, 6), ("rsMiningStationT2", 12, 8), ("rsMiningStationT2Boosted", 12, 12), ("rsMiningStationT3", 16, 16), ("rsMiningStationT3Boosted", 16, 24)):
    if name not in UNITS:
        ERRORS.append(f"missing mining tier {name}")
    elif ("core", "generation_resources", f"credits={credits}, minerals={expected}") not in UNITS[name][1]:
        ERRORS.append(f"{name}: expected credits={credits}, minerals={expected}")
if "rsCruiserMissile" in UNITS:
    entries = UNITS["rsCruiserMissile"][1]
    for expected in (("turret_2", "projectile", "1"), ("turret_2", "limitingRange", "320"), ("turret_2", "delay", "84"), ("turret_3", "projectile", "3"), ("projectile_1", "directDamage", "60"), ("projectile_1", "areaDamage", "140"), ("projectile_1", "areaRadius", "34"), ("projectile_1", "targetSpeed", "9")):
        if expected not in entries:
            ERRORS.append(f"missile cruiser must retain its dual fast-missile salvo: {expected}")
for name, life, resistance, splash in (("rsCruiserMissile", "600", "2", "140"), ("rsMissileBattleship", "650", "3", "150")):
    if name in UNITS:
        entries = UNITS[name][1]
        for expected in (("projectile_1", "life", life), ("projectile_1", "deflectionPower", resistance), ("projectile_1", "areaDamage", splash)):
            if expected not in entries:
                ERRORS.append(f"{name}: heavy missile flight or interception behavior regressed: {expected}")
if "rsMissileBattleship" in UNITS:
    for expected in (("turret_4", "copyFrom", "1"), ("turret_5", "copyFrom", "1"), ("projectile_1", "directDamage", "70")):
        if expected not in UNITS["rsMissileBattleship"][1]:
            ERRORS.append(f"missile battleship must fire a three-missile salvo: {expected}")
for name, use, range_ in (("rsDestroyer", "0.55", "95"), ("rsDestroyerKinetic", "0.65", "65"), ("rsDefensePlatform", "0.45", "95")):
    if name in UNITS:
        for expected in (("turret_pd", "laserDefenceEnergyUse", use), ("turret_pd", "limitingRange", range_)):
            if expected not in UNITS[name][1]:
                ERRORS.append(f"{name}: limited missile interception missing {expected}")
for name, use in (("rsBattleshipT2", "0.25"), ("rsMissileBattleshipT2", "0.25"), ("rsParadoxTitan", "0.16"), ("rsShieldGenerator", "0.20")):
    if name in UNITS and ("turret_laserDefence", "laserDefenceEnergyUse", use) not in UNITS[name][1]:
        ERRORS.append(f"{name}: laser defense energy limit missing")
if "rsIonCannon" in UNITS and ("projectile_1", "instant", "true") not in UNITS["rsIonCannon"][1]:
    ERRORS.append("ion cannon heavy shot must not be missile-interceptable")
for name, main, secondary, cadence in (("rsBattleship", "750", "85", "15"), ("rsBattleshipT2", "850", "125", "10")):
    if name in UNITS:
        entries = UNITS[name][1]
        for expected in (("projectile_1", "directDamage", main), ("projectile_3", "directDamage", secondary), ("turret_2", "delay", cadence)):
            if expected not in entries:
                ERRORS.append(f"{name}: anti-small-ship battery missing {expected}")
for name in ("rsBattleshipT2", "rsMissileBattleshipT2"):
    if name in UNITS and ("core", "maxShield", "3000") not in UNITS[name][1]:
        ERRORS.append(f"{name}: reinforced T2 shield missing")
for name in ("rsCorvette", "rsDestroyer", "rsCruiser", "rsBattleship", "rsTitan", "rsIonCannon"):
    if name in UNITS and ("projectile_1", "laserEffect", "true") not in UNITS[name][1]:
        ERRORS.append(f"{name}: energy main gun should use a beam, not lightning")
for name, life in (("rsCorvetteKinetic", "35"), ("rsDestroyerKinetic", "40")):
    if name in UNITS:
        for expected in (("projectile_1", "life", life), ("projectile_1", "laserEffect", "false")):
            if expected not in UNITS[name][1]:
                ERRORS.append(f"{name}: projectile flight must survive beam visual tuning: {expected}")
for name, life in (("rsCorvette", "8"), ("rsDestroyer", "9"), ("rsCruiser", "10"), ("rsBattleship", "11"), ("rsTitan", "12")):
    if name in UNITS and ("projectile_1", "life", life) not in UNITS[name][1]:
        ERRORS.append(f"{name}: beam visual lifetime should match hull scale")
if "rsMineralPlant" in UNITS:
    entries = UNITS["rsMineralPlant"][1]
    if ("core", "tags", "rsMineralPlant") not in entries or any(s == "core" and k == "generation_resources" for s, k, _ in entries):
        ERRORS.append("mineral plant must boost stations without directly producing minerals")
if "rsEngineer" in UNITS and not any(
    s == "canBuild_mineralPlant" and k == "isLockedAlt" and "rsMineralPlant" in v and "incompleteBuildings=true" in v
    for s, k, v in UNITS["rsEngineer"][1]
):
    ERRORS.append("mineral plant cap must count unfinished construction")
if "rsEngineer" in UNITS:
    entries = UNITS["rsEngineer"][1]
    if ("canBuild_mineralPlant", "isLocked", "if not self.globalTeamTags(includes='rsTechDestroyer')") not in entries or ("canBuild_mineralPlant", "isLockedAltMessage", "本队只能拥有一座矿物处理厂（含在建）") not in entries:
        ERRORS.append("mineral plant technology and team cap must have separate lock messages")

if not (ROOT / "mod-info.txt").is_file():
    ERRORS.append("missing mod-info.txt")

overrides = {(name, v) for name, (_, entries) in UNITS.items() for s, k, v in entries if s == "core" and k == "overrideAndReplace"}
if overrides != {("rsPreFtlCommand", "commandCenter"), ("rsPreFtlBuilder", "builder"), ("rsPreFtlMine", "extractor"), ("rsNativeRepairBay", "repairBay"), ("rsNativeGunT3Bridge", "c_turret_t3_gun"), ("rsNativeSamT3Bridge", "c_antiAirTurretT3")}:
    ERRORS.append(f"native replacements must include capital, builder, extractor, repair bay, and T3 towers: {overrides}")
if "rsNativeRepairBay" in UNITS:
    entries = UNITS["rsNativeRepairBay"][1]
    if ("action_upgradeRepairBase", "convertTo", "rsRepairBase") not in entries:
        ERRORS.append("native repair bay must upgrade to the repair base")
if "rsEngineer" in UNITS:
    entries = UNITS["rsEngineer"][1]
    if ("canBuild_repairBase", "name", "rsNativeRepairBay") not in entries:
        ERRORS.append("engineer must build the native repair bay bridge")
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
            ERRORS.append("planetary defense platform must gain self repair")
        if platform == "rsDefensePlatform" and any(s == "core" and k == "selfRegenRate" for s, k, _ in bridge_entries):
            ERRORS.append("basic defense platform must not self repair")
        for key in ("footprint", "constructionFootprint"):
            if ("core", key, "0,0,0,1") not in platform_entries:
                ERRORS.append(f"{platform} must occupy 1x2")
        if ("core", "displayFootprint", "0,0,0,1") not in platform_entries:
            ERRORS.append(f"{platform} selection frame must match its 1x2 footprint")
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
    if ("action_researchFTL", "tags", "rsFtlResearch") not in entries or not any(s == "action_researchFTL" and k == "isVisible" and "queueSize(withActionTag='rsFtlResearch')==0" in v for s, k, v in entries):
        ERRORS.append("command center must hide FTL research while it is already queued")
    for faction in ("regular", "machine", "hive"):
        if (f"action_{faction}", "price", "credits=5000, minerals=150") not in entries:
            ERRORS.append(f"{faction} empire must pay the new entry cost")
if "rsPreFtlBuilder" in UNITS:
    entries = UNITS["rsPreFtlBuilder"][1]
    if ("action_upgradeEngineer", "convertTo", "rsEngineer") not in entries:
        ERRORS.append("native builder must convert into an engineer")
    if ("core", "canBuild_1_name", "extractor") not in entries:
        ERRORS.append("pre-FTL builder must retain the native extractor menu entry")
    for section, native_name in (("canBuild_landFactory", "landFactory"), ("canBuild_airFactory", "airFactory"), ("canBuild_seaFactory", "seaFactory"), ("canBuild_mechFactory", "mechFactory"), ("canBuild_experimentalLandFactory", "experimentalLandFactory"), ("canBuild_nukeLauncher", "nukeLauncherC")):
        if (section, "name", native_name) not in entries:
            ERRORS.append(f"pre-FTL builder must retain {native_name} for players")
        if (section, "isLocked", "if self.isControlledByAI and self.resource('rsAiHandicap') >= 1.4") not in entries:
            ERRORS.append(f"pre-FTL builder must reserve {native_name} for players and lower-difficulty AI")
if "rsEngineer" in UNITS:
    entries = UNITS["rsEngineer"][1]
    for section, native_name in (("canBuild_landFactory", "landFactory"), ("canBuild_airFactory", "airFactory"), ("canBuild_seaFactory", "seaFactory"), ("canBuild_mechFactory", "mechFactory"), ("canBuild_experimentalLandFactory", "experimentalLandFactory"), ("canBuild_nukeLauncher", "nukeLauncherC")):
        if (section, "name", native_name) not in entries or (section, "isLocked", "if self.isControlledByAI and self.resource('rsAiHandicap') >= 1.4") not in entries:
            ERRORS.append(f"engineer must reserve {native_name} for players and lower-difficulty AI")
if "rsShipyard" in UNITS and ("ai", "buildPriority", "0.32") not in UNITS["rsShipyard"][1]:
    ERRORS.append("AI shipyard priority must support early fleet production")
if "rsCorvette" in UNITS and ("ai", "buildPriority", "0.42") not in UNITS["rsCorvette"][1]:
    ERRORS.append("AI corvette priority must support early fleet production")
for filename in ("starbase.ini", "_starbase_tier_common.ini"):
    entries = list(fields(ROOT / "units" / filename))
    if not any(s == "hiddenAction_aiMassAssault" and k == "autoTrigger" and "rsAiHandicap') >= 1.8" in v and "greaterThan=17, withinRange=700" in v for s, k, v in entries):
        ERRORS.append(f"{filename}: high-difficulty fleet must assemble at least 18 ships")
    if ("hiddenAction_aiMassAssault", "takeResources_maxUnits", "28") not in entries:
        ERRORS.append(f"{filename}: high-difficulty fleet order must include up to 28 ships")
    impossible_trigger = next((v for s, k, v in entries if s == "hiddenAction_aiMassAssaultImpossible" and k == "autoTrigger"), "")
    if "rsAiHandicap') >= 3.7" not in impossible_trigger or "greaterThan=31, withinRange=900" not in impossible_trigger or "greaterThan=11, withinRange=900" not in impossible_trigger:
        ERRORS.append(f"{filename}: Impossible mass assault must require 32 ships including 12 capital ships")
    if ("hiddenAction_aiMassAssaultImpossible", "takeResources_maxUnits", "48") not in entries:
        ERRORS.append(f"{filename}: Impossible mass assault must include up to 48 ships")
for filename in ("shipyard.ini", "mega_shipyard.ini", "juggernaut.ini"):
    entries = list(fields(ROOT / "units" / filename))
    if not any(s == "canBuild_corvette" and k == "isLocked" and "rsAiHandicap') >= 3.7" in v and "rsTechCruiser" in v for s, k, v in entries):
        ERRORS.append(f"{filename}: Impossible AI must favor higher hulls after cruiser research")
for name in ("rsResearchStation", "rsPlanetLab"):
    if name in UNITS:
        entries = UNITS[name][1]
        for project in ("Missiles", "Carrier", "Titan", "Juggernaut"):
            if (f"action_research{project}", "ai_isHighPriority", "if self.resource('rsAiHandicap') >= 1.8") not in entries:
                ERRORS.append(f"{name}: high-difficulty AI must prioritize {project} research")
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
    ("outpost", 48), ("engineer", 32), ("ark", 40), ("science_ship", 40),
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

# Tianji research must be gated by an actually completed nexus, and each factory
# must require the matching discovered ship technology.
for name in ("rsResearchStation", "rsPlanetLab"):
    entries = UNITS[name][1]
    for entry in (
        ("action_researchTianjiEngineering", "isLocked", "if not self.globalTeamTags(includes='rsScienceNexusCompleted')"),
        ("action_researchTianjiEngineering", "addGlobalTeamTags", "rsTechTianjiEngineering"),
        ("action_researchTianjiEngineering", "allowMultipleInQueue", "false"),
    ):
        if entry not in entries:
            ERRORS.append(f"{name}: missing Tianji research contract {entry}")
if ("hiddenAction_announceCompletion", "addGlobalTeamTags", "rsScienceNexusCompleted") not in UNITS["rsScienceNexus"][1]:
    ERRORS.append("science nexus must record its actual completion for Tianji engineering")
institute = UNITS["rsTianjiInstitute"][1]
roll = next(v for s, k, v in institute if s == "hiddenAction_attemptDiscovery" and k == "setUnitMemory")
if roll.count("rnd(") != 1 or not all(f"{name}Weight=select(" in roll for name in ("escort", "battle", "titan")):
    ERRORS.append("Tianji discovery must freeze all available weights and sample once")
for sec, key, value in institute:
    if sec.startswith("hiddenAction_discover") and key == "requireConditional" and "globalTeamTags" in value:
        ERRORS.append("Tianji outcome branches must use the frozen pool, not tags changed by an earlier branch")
for factory in ("rsShipyard", "rsMegaShipyard", "rsJuggernaut"):
    entries = UNITS[factory][1]
    for section, tech in (("riddleEscort", "rsTechRiddleEscort"), ("enigmaBattlecruiser", "rsTechEnigmaBattlecruiser"), ("fallenTitan", "rsTechFallenTitan")):
        if (f"canBuild_{section}", "isLocked", f"if not self.globalTeamTags(includes='{tech}')") not in entries:
            ERRORS.append(f"{factory}: missing lost-empire ship technology gate {section}")
fallen = UNITS["rsFallenTitan"][1]
if "titanPermit" in next(v for s, k, v in fallen if s == "core" and k == "price") or ("hiddenAction_returnTitanPermit", "@copyFrom_skipThisSection", "true") not in fallen:
    ERRORS.append("fallen titan must neither consume nor refund normal titan permits")

if ERRORS:
    print("\n".join(ERRORS), file=sys.stderr)
    raise SystemExit(1)
print(f"Validated {len(UNITS)} units and local sprite references")
