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
    save(name, im)


def cruiser():
    im, d = canvas(64)
    d.polygon([(32, 2), (44, 17), (53, 43), (39, 40), (32, 59), (25, 40), (11, 43), (20, 17)], fill=COLORS["hull"], outline=COLORS["edge"])
    d.polygon([(32, 9), (39, 24), (32, 35), (25, 24)], fill=COLORS["dark"], outline=COLORS["light"])
    d.line((17, 29, 47, 29), fill=COLORS["gold"], width=3)
    d.rectangle((18, 40, 24, 52), fill=COLORS["light"])
    d.rectangle((40, 40, 46, 52), fill=COLORS["light"])
    save("cruiser", im)


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
    ):
        tier2_facility(*args)
    cruiser()
