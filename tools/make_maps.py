"""Generate original symmetric starfield skirmish maps in TMX format."""

from base64 import b64encode
from gzip import compress
from pathlib import Path
from random import Random
from struct import pack
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "maps"
OUT.mkdir(exist_ok=True)

MAPS = [
    ("[p2]Twin_Chokepoints", 120, 90, [(18, 45), (101, 45)]),
    ("[p4]Three_Arms", 140, 140, [(20, 20), (119, 20), (20, 119), (119, 119)]),
    ("[p8]Shattered_Galaxy", 180, 180, [(22, 22), (89, 18), (157, 22), (161, 89), (157, 157), (89, 161), (22, 157), (18, 89)]),
]


def images():
    sheet = Image.new("RGBA", (80, 20), "#080e20")
    draw = ImageDraw.Draw(sheet)
    for i, c in enumerate(("#080e20", "#0d1630", "#111c38", "#09182c")):
        x = i * 20
        draw.rectangle((x, 0, x + 19, 19), fill=c)
        if i:
            draw.point((x + 5 + i, 7), fill="#4e6b9c")
            draw.point((x + 15, 13 - i), fill="#8198bd")
    sheet.save(OUT / "starfield.png")
    marker = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(marker)
    d.ellipse((3, 3, 16, 16), fill="#263e65", outline="#99d9f2", width=2)
    marker.save(OUT / "mineral-node.png")
    rare = Image.new("RGBA", (20, 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(rare)
    d.polygon([(10, 1), (18, 10), (10, 18), (2, 10)], fill="#29565D", outline="#8BE1BB")
    d.ellipse((7, 7, 12, 12), fill="#EBCB78")
    rare.save(OUT / "rare-node.png")
    Image.new("RGBA", (20, 20), (0, 0, 0, 0)).save(OUT / "rare-spawn.png")
    Image.new("RGBA", (20, 20), (0, 0, 0, 0)).save(OUT / "planet-spawn.png")
    Image.new("RGBA", (20, 20), (0, 0, 0, 0)).save(OUT / "black-hole-spawn.png")
    Image.new("RGBA", (40, 20), (0, 0, 0, 0)).save(OUT / "quantum-exit-spawn.png")
    Image.new("RGBA", (640, 20), (0, 0, 0, 0)).save(OUT / "spawn-tiles.png")


def encoded(values):
    return "\n   " + b64encode(compress(pack("<" + "I" * len(values), *values))).decode() + "\n  "


def add_tileset(root, firstgid, name, image, count, columns):
    tileset = SubElement(root, "tileset", firstgid=str(firstgid), name=name, tilewidth="20", tileheight="20", tilecount=str(count), columns=str(columns))
    props = SubElement(tileset, "properties")
    SubElement(props, "property", name="embedded_png", value=b64encode((OUT / image).read_bytes()).decode())
    SubElement(tileset, "image", source=image, width=str(columns * 20), height=str((count // columns) * 20))
    return tileset


def add_property(tile, name, value):
    props = tile.find("properties")
    if props is None:
        props = SubElement(tile, "properties")
    SubElement(props, "property", name=name, value=str(value))


def add_layer(root, name, width, height, values, layer_id):
    layer = SubElement(root, "layer", id=str(layer_id), name=name, width=str(width), height=str(height))
    SubElement(layer, "data", encoding="base64", compression="gzip").text = encoded(values)


def planet_positions(width, height, team_count):
    cx, cy = width // 2, height // 2
    if team_count == 2:
        return [(cx - 18, cy), (cx, cy), (cx + 18, cy)]
    if team_count == 4:
        return [(cx, cy), (cx - 28, cy), (cx + 28, cy), (cx, cy - 28), (cx, cy + 28)]
    return [(cx, cy), (cx - 38, cy), (cx + 38, cy), (cx, cy - 38), (cx, cy + 38),
            (cx - 28, cy - 28), (cx + 28, cy - 28), (cx - 28, cy + 28), (cx + 28, cy + 28)]


def black_hole_positions(width, height, team_count):
    cx, cy = width // 2, height // 2
    if team_count == 2:
        return [(cx, cy - 24), (cx, cy + 24)]
    return [(cx + dx, cy + dy) for dx in (-20, 20) for dy in (-20, 20)]


def quantum_exit_positions(width, height, team_count):
    if team_count == 2:
        return [(40, 20), (80, 70)]
    return [(width // 2, 20 if team_count == 4 else 25),
            (width // 2, height - (20 if team_count == 4 else 25))]


def create_map(name, width, height, spawns):
    rng = Random(name)
    root = Element("map", version="1.2", tiledversion="1.2.1", orientation="orthogonal", renderorder="right-down", width=str(width), height=str(height), tilewidth="20", tileheight="20", infinite="0", nextlayerid="4", nextobjectid="2")
    add_tileset(root, 1, "Starfield", "starfield.png", 4, 4)
    misc = add_tileset(root, 5, "Mineral nodes", "mineral-node.png", 1, 1)
    add_property(SubElement(misc, "tile", id="0"), "res_pool", "")
    units = add_tileset(root, 6, "Starting units", "spawn-tiles.png", 32, 32)
    for team in range(len(spawns)):
        for kind, unit in enumerate(("rsFactionPicker", "rsEngineer", "rsScienceShip", "rsCorvette")):
            tile = SubElement(units, "tile", id=str(4 * team + kind))
            add_property(tile, "team", team)
            add_property(tile, "unit", unit)
    rare = add_tileset(root, 38, "Rare deposits", "rare-node.png", 1, 1)
    add_property(SubElement(rare, "tile", id="0"), "res_pool", "")
    rare_units = add_tileset(root, 39, "Rare deposit markers", "rare-spawn.png", 1, 1)
    rare_tile = SubElement(rare_units, "tile", id="0")
    add_property(rare_tile, "team", "none")
    add_property(rare_tile, "unit", "rsRareDeposit")
    planet_units = add_tileset(root, 40, "Planet markers", "planet-spawn.png", 1, 1)
    planet_tile = SubElement(planet_units, "tile", id="0")
    add_property(planet_tile, "team", "none")
    add_property(planet_tile, "unit", "rsPlanetUnclaimed")
    black_holes = add_tileset(root, 41, "Black hole markers", "black-hole-spawn.png", 1, 1)
    black_hole_tile = SubElement(black_holes, "tile", id="0")
    add_property(black_hole_tile, "team", "none")
    add_property(black_hole_tile, "unit", "rsBlackHole")
    quantum_exits = add_tileset(root, 42, "Quantum exits", "quantum-exit-spawn.png", 2, 2)
    for tile_id, unit in enumerate(("rsQuantumExitA", "rsQuantumExitB")):
        tile = SubElement(quantum_exits, "tile", id=str(tile_id))
        add_property(tile, "team", "none")
        add_property(tile, "unit", unit)

    ground = [1] * (width * height)
    for y in range(height):
        for x in range(width):
            if rng.random() < 0.08:
                ground[y * width + x] = 2 + rng.randrange(3)
    items = [0] * (width * height)
    unit_layer = [0] * (width * height)
    for team, (x, y) in enumerate(spawns):
        unit_layer[y * width + x] = 6 + 4 * team
        unit_layer[y * width + x + (1 if x < width // 2 else -1)] = 7 + 4 * team
        unit_layer[(y + 1) * width + x] = 8 + 4 * team
        for dx, dy in ((-2, -2), (2, -2), (-2, 2), (2, 2)):
            unit_layer[(y + dy) * width + (x + dx)] = 9 + 4 * team
        for dx, dy in ((-7, -5), (7, -5), (-7, 5), (7, 5)):
            nx, ny = x + dx, y + dy
            if 2 <= nx < width - 2 and 2 <= ny < height - 2:
                items[ny * width + nx] = 5
    # Neutral central fields create a shared reason to contest the map.
    for x, y in ((width // 2 - 8, height // 2), (width // 2 + 8, height // 2)):
        items[y * width + x] = 5
    rare_positions = [(width // 2, height // 2 - 12), (width // 2, height // 2 + 12)]
    if len(spawns) >= 8:
        rare_positions += [(width // 2 - 16, height // 2), (width // 2 + 16, height // 2)]
    for x, y in rare_positions:
        items[y * width + x] = 38
        unit_layer[y * width + x] = 39
    for x, y in planet_positions(width, height, len(spawns)):
        assert unit_layer[y * width + x] == 0
        unit_layer[y * width + x] = 40
    for x, y in black_hole_positions(width, height, len(spawns)):
        assert unit_layer[y * width + x] == 0
        unit_layer[y * width + x] = 41
    for index, (x, y) in enumerate(quantum_exit_positions(width, height, len(spawns))):
        assert unit_layer[y * width + x] == 0
        unit_layer[y * width + x] = 42 + index

    add_layer(root, "Ground", width, height, ground, 1)
    add_layer(root, "Items", width, height, items, 2)
    add_layer(root, "Units", width, height, unit_layer, 3)
    group = SubElement(root, "objectgroup", id="4", name="Triggers", visible="0")
    info = SubElement(group, "object", id="1", name="map_info", x="0", y="0", width="100", height="40")
    props = SubElement(info, "properties")
    SubElement(props, "property", name="fog", value="map")
    SubElement(props, "property", name="type", value="Skirmish")
    indent(root)
    ElementTree(root).write(OUT / f"{name}.tmx", encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    images()
    for args in MAPS:
        create_map(*args)
