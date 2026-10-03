"""Generate numbered planet state variants from the authoritative map names."""

from pathlib import Path

from make_maps import PLANET_NAMES


UNITS = Path(__file__).resolve().parents[1] / "mod/rusted-stellaris/units"


def impact_action(name: str, tag: str, result: str, notice: str) -> str:
    return (
        f"[hiddenAction_{name}]\n"
        f"autoTriggerOnEvent: tookDamage(withTag='{tag}')\n"
        f"showMessageToAllPlayers: {notice}\n"
        f"convertTo: {result}\n"
        "takeResources: credits=0\n"
        "takeResources_includeUnitsWithinRange: 48\n"
        "takeResources_includeUnitsWithinRange_team: any\n"
        "takeResources_excludeUnitsWithoutTags: rsPlanetColony\n"
        "takeResources_searchOnly: true\n"
        "takeResources_triggerActionForEach: purgeColony\n\n"
    )


def main() -> None:
    for planets in PLANET_NAMES.values():
        for planet_id, display_name in planets:
            slug = planet_id.lower()
            source = UNITS / f"planet_{slug}.ini"
            intact_name = f"rsPlanet{planet_id}"
            occupied_name = f"{intact_name}Occupied"
            shattered_name = f"{intact_name}Shattered"
            sealed_name = f"{intact_name}Sealed"
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
                "switchToTeam: -1\n\n"
                + impact_action("worldCrack", "rsWorldCracker", shattered_name, f"{display_name}遭地爆天星击中。地壳崩裂，行星已永久破碎，任何殖民地都无法在此重建。")
                + impact_action("pacify", "rsPacifier", sealed_name, f"{display_name}已被安乐天使封存。强光退去后，一道无法穿透的屏障将整颗行星与银河隔绝。")
                + "[hiddenAction_purgeColony]\n"
                "sendMessageTo: thisActionTarget\n"
                "sendMessageWithTags: rsColossusPurge\n"
            )
            source.write_text(base, encoding="utf-8")
            occupied = (
                "[core]\n"
                f"copyFrom: planet_{slug}.ini\n"
                f"name: {occupied_name}\n"
                f"displayText: {display_name}（已殖民）\n"
                f"displayDescription: 编号 {planet_id} 的殖民行星，控制者是邻近殖民地所属队伍。\n"
                f"tags: rsPlanetIntact, rsPlanetOccupied, {intact_name}\n\n"
                "[graphics]\n"
                "image: planet_occupied.png\n\n"
                "[action_markOccupied]\n"
                "autoTrigger: false\n\n"
                "[action_markUnclaimed]\n"
                "autoTrigger: if nearestUnit(withinRange=48, withTag='rsPlanetColony', relation='any', incompleteBuildings=false) == null\n"
                f"convertTo: {intact_name}\n\n"
                + impact_action("neutronSweep", "rsNeutronSweep", intact_name, f"{display_name}上空的中子羽流正在散去。殖民地已被清除，行星仍可重新殖民。").rstrip() + "\n"
            )
            (UNITS / f"planet_{slug}_occupied.ini").write_text(occupied, encoding="utf-8")
            for state, label, image, unit_name in (
                ("shattered", "已破碎", "planet_shattered.png", shattered_name),
                ("sealed", "已封存", "planet_sealed.png", sealed_name),
            ):
                terminal = (
                    "[core]\n"
                    "copyFrom: planet_unclaimed.ini\n"
                    f"name: {unit_name}\n"
                    f"displayText: {display_name}（{label}）\n"
                    f"displayDescription: 编号 {planet_id} 的永久{label}行星，本局不可再殖民。\n"
                    f"tags: rsPlanet{state.title()}, {intact_name}\n"
                    "canOnlyBeAttackedByUnitsWithTags: rsNeverAttackTerminalPlanet\n\n"
                    "[graphics]\n"
                    f"image: {image}\n\n"
                    "[action_keepNeutral]\n"
                    "autoTrigger: if self.teamId() != -1\n"
                    "switchToTeam: -1\n"
                )
                (UNITS / f"planet_{slug}_{state}.ini").write_text(terminal, encoding="utf-8")


if __name__ == "__main__":
    main()
