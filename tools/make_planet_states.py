"""Generate numbered occupied-planet variants from the authoritative map names."""

from pathlib import Path

from make_maps import PLANET_NAMES


UNITS = Path(__file__).resolve().parents[1] / "mod/rusted-stellaris/units"


def main() -> None:
    for planets in PLANET_NAMES.values():
        for planet_id, display_name in planets:
            slug = planet_id.lower()
            source = UNITS / f"planet_{slug}.ini"
            intact_name = f"rsPlanet{planet_id}"
            occupied_name = f"{intact_name}Occupied"
            base = (
                "[core]\n"
                "copyFrom: planet_unclaimed.ini\n"
                f"name: {intact_name}\n"
                f"displayText: {display_name}\n"
                f"displayDescription: 编号 {planet_id} 的无主行星。工程船可在其附近建立殖民地。\n"
                f"tags: rsPlanetIntact, {intact_name}\n\n"
                "[graphics]\n"
                "image: planet_unclaimed.png\n\n"
                "[action_markOccupied]\n"
                "autoTrigger: if nearestUnit(withinRange=48, withTag='rsPlanetColony', relation='any', incompleteBuildings=false) != null\n"
                f"convertTo: {occupied_name}\n\n"
                "[action_keepNeutral]\n"
                "autoTrigger: if self.teamId() != -1\n"
                "switchToTeam: -1\n"
            )
            source.write_text(base, encoding="utf-8")
            occupied = (
                "[core]\n"
                f"copyFrom: planet_{slug}.ini\n"
                f"name: {occupied_name}\n"
                f"displayText: {display_name}（已殖民）\n"
                f"displayDescription: 编号 {planet_id} 的殖民行星；控制者是邻近殖民地所属队伍。\n"
                f"tags: rsPlanetIntact, rsPlanetOccupied, {intact_name}\n\n"
                "[graphics]\n"
                "image: planet_occupied.png\n\n"
                "[action_markOccupied]\n"
                "autoTrigger: false\n\n"
                "[action_markUnclaimed]\n"
                "autoTrigger: if nearestUnit(withinRange=48, withTag='rsPlanetColony', relation='any', incompleteBuildings=false) == null\n"
                f"convertTo: {intact_name}\n"
            )
            (UNITS / f"planet_{slug}_occupied.ini").write_text(occupied, encoding="utf-8")


if __name__ == "__main__":
    main()
