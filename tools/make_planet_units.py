"""Generate individually named neutral planet units for the three starfields."""

from pathlib import Path

from make_maps import PLANET_NAMES

OUT = Path(__file__).resolve().parents[1] / "mod" / "rusted-stellaris" / "units"

for planets in PLANET_NAMES.values():
    for planet_id, display_name in planets:
        (OUT / f"planet_{planet_id.lower()}.ini").write_text(
            "[core]\n"
            "copyFrom: planet_unclaimed.ini\n"
            f"name: rsPlanet{planet_id}\n"
            f"displayText: {display_name}\n"
            f"displayDescription: 编号 {planet_id} 的无主行星。工程船可在其附近建立殖民地。\n"
            f"tags: rsPlanetIntact, rsPlanet{planet_id}\n"
            "\n[graphics]\n"
            "image: planet_unclaimed.png\n",
            encoding="utf-8",
        )
