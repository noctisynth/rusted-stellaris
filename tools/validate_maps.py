"""Validate generated TMX layers and balanced starting positions."""

from base64 import b64decode
from gzip import decompress
from pathlib import Path
from struct import unpack
from xml.etree.ElementTree import parse

ROOT = Path(__file__).resolve().parents[1] / "maps"
EXPECTED = {"[p2]Twin_Chokepoints.tmx": 2, "[p4]Three_Arms.tmx": 4, "[p8]Shattered_Galaxy.tmx": 8}
PLANET_COUNT = {2: 3, 4: 5, 8: 9}


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
    assert set(layers) == {"Ground", "Items", "Units"}
    assert all(gid in (1, 2, 3, 4) for gid in layers["Ground"])
    spawns = []
    for team in range(team_count):
        command_gid, builder_gid = 6 + 4 * team, 7 + 4 * team
        assert layers["Units"].count(command_gid) == 1, (filename, team, "command center")
        assert layers["Units"].count(builder_gid) == 1, (filename, team, "builder")
        assert layers["Units"].count(8 + 4 * team) == 1, (filename, team, "science ship")
        assert layers["Units"].count(9 + 4 * team) == 4, (filename, team, "corvettes")
        index = layers["Units"].index(command_gid)
        spawns.append((index % width, index // width))
    assert layers["Items"].count(5) >= 4 * team_count + 2
    assert layers["Items"].count(38) == (4 if team_count >= 8 else 2)
    assert layers["Units"].count(39) == layers["Items"].count(38)
    assert layers["Units"].count(40) == PLANET_COUNT[team_count]
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
            assert definitions == {(team, unit) for team in range(team_count) for unit in ("commandCenter", "builder", "rsScienceShip", "rsCorvette")}
        if tileset.attrib["name"] == "Rare deposit markers":
            properties = {p.attrib["name"]: p.attrib["value"] for p in tileset.findall("./tile/properties/property")}
            assert properties == {"team": "none", "unit": "rsRareDeposit"}
        if tileset.attrib["name"] == "Planet markers":
            properties = {p.attrib["name"]: p.attrib["value"] for p in tileset.findall("./tile/properties/property")}
            assert properties == {"team": "none", "unit": "rsPlanetUnclaimed"}
    print(f"{filename}: {team_count} teams, {layers['Items'].count(5)} mineral pools, {layers['Items'].count(38)} rare deposits, {layers['Units'].count(40)} planets")
