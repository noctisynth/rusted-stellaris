"""Validate generated TMX layers and balanced starting positions."""

from base64 import b64decode
from gzip import decompress
from pathlib import Path
from struct import unpack
from xml.etree.ElementTree import parse

ROOT = Path(__file__).resolve().parents[1] / "maps"
EXPECTED = {"[p2]Twin_Chokepoints.tmx": 2, "[p4]Three_Arms.tmx": 4, "[p8]Shattered_Galaxy.tmx": 8}


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
        command_gid, builder_gid = 6 + 2 * team, 7 + 2 * team
        assert layers["Units"].count(command_gid) == 1, (filename, team, "command center")
        assert layers["Units"].count(builder_gid) == 1, (filename, team, "builder")
        index = layers["Units"].index(command_gid)
        spawns.append((index % width, index // width))
    assert layers["Items"].count(5) >= 4 * team_count + 2
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
    print(f"{filename}: {team_count} teams, {layers['Items'].count(5)} resource pools")
