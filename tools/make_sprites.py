"""Draw original placeholder sprites for the first playable unit chain."""

from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / "mod" / "rusted-stellaris" / "units"

COLORS = {
    "hull": "#718bb1",
    "edge": "#b7d4ed",
    "dark": "#263650",
    "light": "#6fe3f0",
    "gold": "#efc66c",
    "wreck": "#4a4d58",
}


def canvas(size=64):
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def save(name, image):
    image.save(OUT / f"{name}.png")
    wreck = image.copy()
    pixels = wreck.load()
    for y in range(wreck.height):
        for x in range(wreck.width):
            r, g, b, a = pixels[x, y]
            if a:
                gray = int(0.22 * r + 0.28 * g + 0.20 * b)
                pixels[x, y] = (gray + 15, gray + 10, gray + 9, a)
    wreck.save(OUT / f"{name}_dead.png")


def starbase():
    im, d = canvas()
    d.ellipse((8, 8, 55, 55), fill=COLORS["dark"], outline=COLORS["edge"], width=3)
    d.ellipse((17, 17, 46, 46), outline=COLORS["gold"], width=4)
    d.rectangle((26, 3, 37, 61), fill=COLORS["hull"], outline=COLORS["edge"])
    d.rectangle((3, 26, 61, 37), fill=COLORS["hull"], outline=COLORS["edge"])
    d.ellipse((24, 24, 39, 39), fill=COLORS["light"], outline=COLORS["dark"], width=2)
    save("starbase", im)


def engineer():
    im, d = canvas(32)
    d.polygon([(16, 2), (25, 23), (16, 19), (7, 23)], fill=COLORS["hull"], outline=COLORS["edge"])
    d.rectangle((13, 12, 19, 23), fill=COLORS["light"])
    d.rectangle((8, 24, 12, 29), fill=COLORS["gold"])
    d.rectangle((20, 24, 24, 29), fill=COLORS["gold"])
    save("engineer", im)


def generator():
    im, d = canvas(48)
    d.rectangle((6, 8, 41, 39), fill=COLORS["dark"], outline=COLORS["edge"], width=3)
    for x in (14, 24, 34):
        d.line((x, 10, x, 38), fill=COLORS["gold"], width=4)
    d.ellipse((16, 16, 31, 31), fill=COLORS["light"], outline=COLORS["edge"], width=2)
    save("generator", im)


def shipyard():
    im, d = canvas(64)
    d.arc((7, 7, 56, 56), 25, 155, fill=COLORS["edge"], width=6)
    d.arc((7, 7, 56, 56), 205, 335, fill=COLORS["edge"], width=6)
    d.rectangle((5, 26, 18, 38), fill=COLORS["hull"], outline=COLORS["gold"], width=2)
    d.rectangle((45, 26, 58, 38), fill=COLORS["hull"], outline=COLORS["gold"], width=2)
    d.polygon([(32, 13), (42, 45), (32, 39), (22, 45)], fill=COLORS["dark"], outline=COLORS["light"])
    save("shipyard", im)


def corvette():
    im, d = canvas(32)
    d.polygon([(16, 1), (25, 19), (29, 25), (20, 23), (16, 30), (12, 23), (3, 25), (7, 19)], fill=COLORS["hull"], outline=COLORS["edge"])
    d.polygon([(16, 6), (20, 20), (16, 17), (12, 20)], fill=COLORS["light"])
    d.rectangle((7, 22, 11, 28), fill=COLORS["gold"])
    d.rectangle((21, 22, 25, 28), fill=COLORS["gold"])
    save("corvette", im)


def science_ship():
    im, d = canvas(32)
    d.polygon([(16, 2), (24, 13), (22, 24), (16, 20), (10, 24), (8, 13)], fill=COLORS["hull"], outline=COLORS["edge"])
    d.ellipse((12, 8, 20, 16), fill=COLORS["light"])
    d.line((5, 7, 10, 14), fill=COLORS["gold"], width=2)
    d.line((27, 7, 22, 14), fill=COLORS["gold"], width=2)
    save("science_ship", im)


def mining_station():
    im, d = canvas(48)
    d.polygon([(24, 3), (43, 14), (43, 34), (24, 45), (5, 34), (5, 14)], fill=COLORS["dark"], outline=COLORS["edge"])
    d.rectangle((15, 15, 33, 33), fill=COLORS["hull"], outline=COLORS["gold"], width=2)
    for x in (8, 40):
        d.line((x, 9, x, 39), fill=COLORS["light"], width=3)
    save("mining_station", im)


def research_station():
    im, d = canvas(48)
    d.ellipse((7, 7, 40, 40), outline=COLORS["edge"], width=4)
    d.line((24, 2, 24, 46), fill=COLORS["hull"], width=5)
    d.line((2, 24, 46, 24), fill=COLORS["hull"], width=5)
    d.ellipse((17, 17, 31, 31), fill=COLORS["light"], outline=COLORS["gold"], width=2)
    save("research_station", im)


def outpost():
    im, d = canvas(48)
    d.ellipse((8, 8, 39, 39), fill=COLORS["dark"], outline=COLORS["edge"], width=3)
    d.rectangle((20, 2, 28, 46), fill=COLORS["hull"], outline=COLORS["gold"])
    d.rectangle((2, 20, 46, 28), fill=COLORS["hull"], outline=COLORS["gold"])
    d.ellipse((19, 19, 29, 29), fill=COLORS["light"])
    save("outpost", im)


def destroyer():
    im, d = canvas(48)
    d.polygon([(24, 2), (37, 15), (41, 35), (31, 31), (24, 45), (17, 31), (7, 35), (11, 15)], fill=COLORS["hull"], outline=COLORS["edge"])
    d.polygon([(24, 8), (31, 20), (24, 26), (17, 20)], fill=COLORS["dark"], outline=COLORS["light"])
    d.rectangle((13, 25, 17, 34), fill=COLORS["gold"])
    d.rectangle((31, 25, 35, 34), fill=COLORS["gold"])
    save("destroyer", im)


def tier2_facility(name, motif, accent):
    im, d = canvas(48)
    d.polygon([(24, 3), (42, 12), (45, 34), (31, 44), (16, 44), (3, 34), (6, 12)], fill=COLORS["dark"], outline=COLORS["edge"])
    d.rectangle((10, 10, 37, 37), outline=COLORS["hull"], width=3)
    if motif == "bars":
        for x in (15, 23, 31):
            d.rectangle((x, 17, x + 3, 32), fill=accent)
    elif motif == "flame":
        d.polygon([(24, 9), (31, 22), (27, 34), (19, 34), (16, 23)], fill=accent, outline=COLORS["gold"])
    elif motif == "orb":
        d.ellipse((15, 15, 32, 32), fill=accent, outline=COLORS["edge"], width=2)
        d.line((23, 5, 23, 15), fill=COLORS["gold"], width=2)
    elif motif == "diamond":
        d.polygon([(24, 11), (35, 24), (24, 36), (12, 24)], fill=accent, outline=COLORS["gold"])
    elif motif == "cross":
        d.rectangle((20, 12, 27, 36), fill=accent)
        d.rectangle((12, 20, 35, 27), fill=accent)
    elif motif == "turret":
        d.ellipse((14, 14, 33, 33), fill=COLORS["hull"], outline=accent, width=2)
        d.rectangle((20, 4, 27, 20), fill=accent)
    elif motif == "missile":
        d.polygon([(16, 33), (16, 13), (21, 8), (25, 13), (25, 33)], fill=accent, outline=COLORS["gold"])
        d.polygon([(28, 33), (28, 13), (33, 8), (37, 13), (37, 33)], fill=accent, outline=COLORS["gold"])
    elif motif == "ion":
        d.rectangle((20, 4, 28, 31), fill=COLORS["hull"], outline=accent, width=2)
        d.ellipse((17, 16, 31, 30), fill=accent, outline=COLORS["light"], width=2)
    elif motif == "shield":
        d.arc((12, 11, 36, 36), 190, 530, fill=accent, width=4)
        d.ellipse((19, 19, 29, 29), fill=COLORS["light"])
    save(name, im)


def cruiser():
    im, d = canvas(64)
    d.polygon([(32, 2), (44, 17), (53, 43), (39, 40), (32, 59), (25, 40), (11, 43), (20, 17)], fill=COLORS["hull"], outline=COLORS["edge"])
    d.polygon([(32, 9), (39, 24), (32, 35), (25, 24)], fill=COLORS["dark"], outline=COLORS["light"])
    d.line((17, 29, 47, 29), fill=COLORS["gold"], width=3)
    d.rectangle((18, 40, 24, 52), fill=COLORS["light"])
    d.rectangle((40, 40, 46, 52), fill=COLORS["light"])
    save("cruiser", im)


def faction_picker():
    im, d = canvas(64)
    d.ellipse((5, 5, 58, 58), fill=COLORS["dark"], outline=COLORS["edge"], width=4)
    d.pieslice((13, 13, 50, 50), 210, 330, fill="#69B8E0")
    d.pieslice((13, 13, 50, 50), 330, 90, fill="#EACB58")
    d.pieslice((13, 13, 50, 50), 90, 210, fill="#8CC871")
    d.ellipse((25, 25, 38, 38), fill=COLORS["dark"], outline=COLORS["edge"], width=2)
    save("faction_picker", im)


def starbase_variant(name, accent):
    im = Image.open(OUT / "starbase.png").convert("RGBA")
    pixels = im.load()
    light = tuple(bytes.fromhex(COLORS["light"].lstrip("#")))
    replacement = tuple(bytes.fromhex(accent.lstrip("#")))
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = pixels[x, y]
            if (r, g, b) == light and a:
                pixels[x, y] = (*replacement, a)
    save(name, im)


def faction_facility(name, accent, motif):
    im, d = canvas(48)
    d.ellipse((5, 5, 42, 42), fill=COLORS["dark"], outline=accent, width=3)
    d.rectangle((14, 14, 33, 33), fill=COLORS["hull"], outline=COLORS["edge"], width=2)
    if motif == "spokes":
        for p in ((24, 2, 24, 14), (24, 34, 24, 46), (2, 24, 14, 24), (34, 24, 46, 24)):
            d.line(p, fill=accent, width=4)
        d.ellipse((19, 19, 28, 28), fill=COLORS["light"])
    elif motif == "gears":
        d.ellipse((17, 17, 30, 30), fill=accent, outline=COLORS["dark"], width=2)
        for x, y in ((9, 23), (36, 23), (23, 9), (23, 36)):
            d.rectangle((x, y, x + 3, y + 3), fill=accent)
    else:
        d.ellipse((15, 15, 32, 32), fill=accent)
        d.ellipse((20, 20, 27, 27), fill=COLORS["dark"])
    save(name, im)


def repair_drone():
    im, d = canvas(32)
    d.ellipse((7, 7, 24, 24), fill=COLORS["dark"], outline="#EACB58", width=2)
    d.rectangle((13, 2, 18, 29), fill=COLORS["hull"])
    d.rectangle((2, 13, 29, 18), fill=COLORS["hull"])
    d.ellipse((12, 12, 19, 19), fill="#EACB58")
    save("repair_drone", im)


def swarm_ship():
    im, d = canvas(32)
    d.polygon([(16, 1), (23, 12), (29, 26), (17, 22), (16, 30), (15, 22), (3, 26), (9, 12)], fill="#4D785C", outline="#A7DE89")
    d.ellipse((12, 10, 20, 20), fill="#94DC7C", outline=COLORS["dark"], width=2)
    save("swarm_ship", im)


def weapon_variant(base, name, accent, marks):
    im = Image.open(OUT / f"{base}.png").convert("RGBA")
    d = ImageDraw.Draw(im)
    for x, y, w, h in marks:
        d.rectangle((x, y, x + w, y + h), fill=accent, outline=COLORS["dark"])
    save(name, im)


def battleship():
    im, d = canvas(80)
    d.polygon([(40, 2), (55, 18), (65, 57), (52, 53), (40, 76), (28, 53), (15, 57), (25, 18)], fill=COLORS["hull"], outline=COLORS["edge"])
    d.polygon([(40, 8), (48, 31), (40, 52), (32, 31)], fill=COLORS["dark"], outline=COLORS["light"])
    d.rectangle((36, 3, 44, 27), fill="#78B8FF")
    d.rectangle((22, 43, 29, 64), fill=COLORS["gold"])
    d.rectangle((51, 43, 58, 64), fill=COLORS["gold"])
    save("battleship", im)
    weapon_variant("battleship", "battleship_missile", "#EEA76B", [(16, 24, 10, 8), (54, 24, 10, 8), (32, 55, 16, 7)])


def titan():
    im, d = canvas(96)
    d.polygon([(48, 2), (64, 19), (76, 63), (62, 58), (48, 93), (34, 58), (20, 63), (32, 19)], fill=COLORS["dark"], outline=COLORS["edge"])
    d.polygon([(48, 9), (57, 30), (48, 65), (39, 30)], fill=COLORS["hull"], outline="#B18CFF")
    d.rectangle((43, 3, 53, 38), fill="#B18CFF", outline=COLORS["edge"])
    for x in (22, 64):
        d.rectangle((x, 38, x + 10, 73), fill=COLORS["hull"], outline=COLORS["gold"], width=2)
    d.ellipse((41, 65, 55, 79), fill=COLORS["light"], outline=COLORS["gold"], width=2)
    save("titan", im)


def juggernaut():
    im, d = canvas(96)
    d.polygon([(48, 3), (68, 20), (80, 79), (58, 69), (48, 91), (38, 69), (16, 79), (28, 20)], fill=COLORS["dark"], outline=COLORS["edge"])
    d.rectangle((31, 25, 65, 67), fill=COLORS["hull"], outline=COLORS["gold"], width=3)
    d.rectangle((37, 31, 59, 62), fill=COLORS["dark"], outline=COLORS["light"], width=2)
    for x in (21, 69):
        d.rectangle((x, 41, x + 7, 70), fill=COLORS["hull"], outline=COLORS["gold"], width=2)
    d.polygon([(48, 8), (55, 27), (48, 35), (41, 27)], fill=COLORS["light"], outline=COLORS["edge"])
    save("juggernaut", im)


def carrier_and_craft():
    im, d = canvas(64)
    d.polygon([(32, 3), (47, 22), (54, 55), (39, 46), (32, 59), (25, 46), (10, 55), (17, 22)], fill=COLORS["hull"], outline=COLORS["edge"])
    d.rectangle((22, 19, 42, 43), fill=COLORS["dark"], outline=COLORS["gold"], width=2)
    d.line((32, 19, 32, 43), fill=COLORS["light"], width=3)
    save("carrier_cruiser", im)
    im, d = canvas(24)
    d.polygon([(12, 2), (20, 18), (12, 15), (4, 18)], fill=COLORS["hull"], outline=COLORS["edge"])
    d.rectangle((10, 9, 14, 14), fill=COLORS["light"])
    save("fighter", im)
    im, d = canvas(24)
    d.polygon([(12, 2), (17, 10), (23, 20), (12, 16), (1, 20), (7, 10)], fill=COLORS["dark"], outline=COLORS["gold"])
    d.ellipse((9, 7, 15, 13), fill="#F2C979")
    save("strike_craft", im)


def fortified_starbase(name, ring_count, accent):
    im, d = canvas(96)
    d.ellipse((11, 11, 84, 84), fill=COLORS["dark"], outline=COLORS["edge"], width=4)
    for ring in range(ring_count):
        inset = 17 + ring * 9
        d.ellipse((inset, inset, 95 - inset, 95 - inset), outline=accent, width=3)
    d.rectangle((41, 4, 54, 91), fill=COLORS["hull"], outline=COLORS["edge"], width=2)
    d.rectangle((4, 41, 91, 54), fill=COLORS["hull"], outline=COLORS["edge"], width=2)
    d.ellipse((39, 39, 56, 56), fill=COLORS["light"], outline=COLORS["gold"], width=2)
    for x, y in ((15, 15), (69, 15), (15, 69), (69, 69)):
        d.rectangle((x, y, x + 11, y + 11), fill=accent, outline=COLORS["dark"], width=2)
    save(name, im)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for draw in (starbase, engineer, generator, shipyard, corvette, science_ship, mining_station, research_station, outpost, destroyer):
        draw()
    for args in (
        ("mineral_plant", "bars", "#C46C62"),
        ("foundry", "flame", "#F47E45"),
        ("planet_lab", "orb", "#69B8E0"),
        ("trade_hub", "diamond", "#EACB58"),
        ("defense_platform", "turret", "#79C8EE"),
        ("repair_base", "cross", "#6FCB9A"),
        ("strategic_extractor", "diamond", "#8BE1BB"),
        ("missile_platform", "missile", "#EEA76B"),
        ("ion_cannon", "ion", "#91C6FA"),
        ("shield_generator", "shield", "#8DB5F0"),
    ):
        tier2_facility(*args)
    cruiser()
    faction_picker()
    starbase_variant("starbase_machine", "#EACB58")
    starbase_variant("starbase_hive", "#8CC871")
    for args in (
        ("administration", "#69B8E0", "spokes"),
        ("assembly", "#EACB58", "gears"),
        ("hatchery", "#8CC871", "core"),
    ):
        faction_facility(*args)
    repair_drone()
    swarm_ship()
    weapon_variant("corvette", "corvette_kinetic", "#F2C979", [(5, 15, 7, 4), (20, 15, 7, 4)])
    weapon_variant("destroyer", "destroyer_kinetic", "#F2C979", [(8, 19, 9, 5), (31, 19, 9, 5)])
    weapon_variant("cruiser", "cruiser_missile", "#EEA76B", [(12, 22, 10, 8), (42, 22, 10, 8)])
    battleship()
    titan()
    juggernaut()
    carrier_and_craft()
    fortified_starbase("starhold", 1, "#69B8E0")
    fortified_starbase("fortress", 2, "#F2C979")
    fortified_starbase("citadel", 3, "#E58CAB")
    Image.new("RGBA", (20, 20), (0, 0, 0, 0)).save(OUT / "rare_deposit.png")
