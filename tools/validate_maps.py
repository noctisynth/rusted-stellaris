"""Validate generated TMX layers and balanced starting positions."""

from base64 import b64decode
from gzip import decompress
from pathlib import Path
from struct import unpack
from xml.etree.ElementTree import parse

from make_maps import PLANET_NAMES, planet_positions

ROOT = Path(__file__).resolve().parents[1] / "maps"
UNITS = ROOT.parent / "mod" / "rusted-stellaris" / "units"
EXPECTED = {"[p2]Twin_Chokepoints.tmx": 2, "[p4]Three_Arms.tmx": 4, "[p8]Shattered_Galaxy.tmx": 8}
PLANET_COUNT = {2: 3, 4: 5, 8: 9}
BLACK_HOLE_COUNT = {2: 2, 4: 4, 8: 4}

all_planets = [entry for entries in PLANET_NAMES.values() for entry in entries]
assert len(all_planets) == 17
assert len({planet_id for planet_id, _ in all_planets}) == len(all_planets)
assert len({display_name for _, display_name in all_planets}) == len(all_planets)
for planet_id, display_name in all_planets:
    source = (UNITS / f"planet_{planet_id.lower()}.ini").read_text(encoding="utf-8")
    assert f"name: rsPlanet{planet_id}\n" in source
    assert f"displayText: {display_name}\n" in source
    assert f"tags: rsPlanetIntact, rsPlanet{planet_id}\n" in source


def layer_values(layer, count):
    data = layer.find("data")
    assert data is not None and data.attrib == {"encoding": "base64", "compression": "gzip"}
    raw = decompress(b64decode(data.text or ""))
    assert len(raw) == count * 4
    return unpack("<" + "I" * count, raw)


for filename, team_count in EXPECTED.items():
    path = ROOT / filename
    xml = parse(path).getroot()
    width, height = int(xml.attrib["width"]), int(xml.attrib["height"])
    layers = {layer.attrib["name"]: layer_values(layer, width * height) for layer in xml.findall("layer")}
    triggers = xml.find("objectgroup")
    assert triggers is not None
    for team in range(team_count):
        detector_id = f"capitalLost{team}"
        detector = next((obj for obj in triggers.findall("object") if obj.attrib.get("name") == f"Capital lost {team}"), None)
        surrender = next((obj for obj in triggers.findall("object") if obj.attrib.get("name") == f"Capital surrender {team}"), None)
        assert detector is not None and surrender is not None
        assert detector.attrib["type"] == "unitDetect" and surrender.attrib["type"] == "unitRemove"
        assert detector.attrib["width"] == surrender.attrib["width"] == str(width * 20)
        assert detector.attrib["height"] == surrender.attrib["height"] == str(height * 20)
        detector_props = {p.attrib["name"]: p.attrib["value"] for p in detector.findall("./properties/property")}
        surrender_props = {p.attrib["name"]: p.attrib["value"] for p in surrender.findall("./properties/property")}
        assert detector_props == {"id": detector_id, "team": str(team), "onlyWithTag": "rsCapital", "maxUnits": "0", "warmup": "1s"}
        assert surrender_props == {"team": str(team), "activatedBy": detector_id}
    assert set(layers) == {"Ground", "Items", "Units"}
    assert all(gid in (1, 2, 3, 4) for gid in layers["Ground"])
    spawns = []
    for team in range(team_count):
        picker_gid, engineer_gid = 6 + 4 * team, 7 + 4 * team
        assert layers["Units"].count(picker_gid) == 1, (filename, team, "faction picker")
        assert layers["Units"].count(engineer_gid) == 1, (filename, team, "engineer")
        assert layers["Units"].count(8 + 4 * team) == 1, (filename, team, "science ship")
        assert layers["Units"].count(9 + 4 * team) == 4, (filename, team, "corvettes")
        index = layers["Units"].index(picker_gid)
        spawns.append((index % width, index // width))
    assert layers["Items"].count(5) >= 4 * team_count + 2
    assert layers["Items"].count(38) == (4 if team_count >= 8 else 2)
    assert layers["Units"].count(39) == layers["Items"].count(38)
    assert len(PLANET_NAMES[team_count]) == PLANET_COUNT[team_count]
    for index, (x, y) in enumerate(planet_positions(width, height, team_count)):
        assert layers["Units"].count(40 + index) == 1
        assert layers["Units"][y * width + x] == 40 + index
    assert layers["Units"].count(49) == BLACK_HOLE_COUNT[team_count]
    assert layers["Units"].count(50) == 1 and layers["Units"].count(51) == 1
    assert all(unit_gid != 39 or layers["Items"][index] == 38 for index, unit_gid in enumerate(layers["Units"]))
    for x, y in spawns:
        nearby = sum(
            1
            for yy in range(max(0, y - 8), min(height, y + 9))
            for xx in range(max(0, x - 8), min(width, x + 9))
            if layers["Items"][yy * width + xx] == 5
        )
        assert nearby >= 4, (filename, (x, y), nearby)
    for tileset in xml.findall("tileset"):
        image = tileset.find("image")
        assert image is not None and (ROOT / image.attrib["source"]).is_file()
        embedded = [p.attrib["value"] for p in tileset.findall("./properties/property") if p.attrib["name"] == "embedded_png"]
        assert len(embedded) == 1 and b64decode(embedded[0]) == (ROOT / image.attrib["source"]).read_bytes()
        if tileset.attrib["name"] == "Starting units":
            definitions = {
                (int(next(p.attrib["value"] for p in tile.findall("./properties/property") if p.attrib["name"] == "team")),
                 next(p.attrib["value"] for p in tile.findall("./properties/property") if p.attrib["name"] == "unit"))
                for tile in tileset.findall("tile")
            }
            assert definitions == {(team, unit) for team in range(team_count) for unit in ("rsStarbaseOrigin", "rsEngineer", "rsScienceShip", "rsCorvette")}
        if tileset.attrib["name"] == "Rare deposit markers":
            properties = {p.attrib["name"]: p.attrib["value"] for p in tileset.findall("./tile/properties/property")}
            assert properties == {"team": "none", "unit": "rsRareDeposit"}
        if tileset.attrib["name"] == "Planet markers":
            definitions = [
                {p.attrib["name"]: p.attrib["value"] for p in tile.findall("./properties/property")}
                for tile in tileset.findall("tile")
            ]
            assert definitions == [
                {"team": "none", "unit": f"rsPlanet{planet_id}"}
                for planet_id, _ in PLANET_NAMES[team_count]
            ]
        if tileset.attrib["name"] == "Black hole markers":
            properties = {p.attrib["name"]: p.attrib["value"] for p in tileset.findall("./tile/properties/property")}
            assert properties == {"team": "none", "unit": "rsBlackHole"}
        if tileset.attrib["name"] == "Quantum exits":
            definitions = [
                {p.attrib["name"]: p.attrib["value"] for p in tile.findall("./properties/property")}
                for tile in tileset.findall("tile")
            ]
            assert definitions == [
                {"team": "none", "unit": "rsQuantumExitA"},
                {"team": "none", "unit": "rsQuantumExitB"},
            ]
    print(f"{filename}: {team_count} teams, {layers['Items'].count(5)} mineral pools, {layers['Items'].count(38)} rare deposits, {PLANET_COUNT[team_count]} named planets, {layers['Units'].count(49)} black holes, 2 quantum exits")
