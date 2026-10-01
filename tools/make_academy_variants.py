"""Regenerate the persistent fleet-academy variants from normal combat hulls."""

from pathlib import Path


UNITS = Path(__file__).resolve().parents[1] / "mod" / "rusted-stellaris" / "units"
HULLS = (
    "corvette", "corvette_kinetic", "fighter", "strike_craft", "swarm_ship",
    "destroyer", "destroyer_kinetic", "cruiser", "cruiser_missile",
    "carrier_cruiser", "battleship", "battleship_missile", "titan", "juggernaut",
)


def field(path: Path, key: str, section_name: str = "core") -> str | None:
    section = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
        elif section == section_name and line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    return None


def inherited_field(path: Path, key: str, section_name: str = "core") -> str:
    value = field(path, key, section_name)
    if value is not None:
        return value
    parent = field(path, "copyFrom")
    if parent is None:
        raise ValueError(f"{path.name} has no {key}")
    if "," in parent:
        raise ValueError(f"{path.name} has ambiguous copyFrom")
    return inherited_field(path.parent / parent, key, section_name)


def main() -> None:
    for hull in HULLS:
        source = UNITS / f"{hull}.ini"
        name = field(source, "name")
        display = field(source, "displayText")
        hp = int(inherited_field(source, "maxHp"))
        tags = inherited_field(source, "tags")
        image = inherited_field(source, "image", "graphics")
        wreck = inherited_field(source, "image_wreak", "graphics")
        if not name or not display:
            raise ValueError(f"{source.name} lacks unit identity")
        veteran_name = name + "Veteran"
        target = UNITS / f"{hull}_veteran.ini"
        result = (
            "[core]\n"
            f"copyFrom: {source.name}\n"
            f"name: {veteran_name}\n"
            f"displayText: 精锐{display}\n"
            f"maxHp: {int(hp * 1.15 + 0.5)}\n"
            f"tags: {tags}, rsVeteran\n\n"
            "[graphics]\n"
            f"image: {image}\n"
            f"image_wreak: {wreck}\n\n"
            "[attack]\n"
            "shootDamageMultiplier: 1.1\n"
        )
        target.write_text(result, encoding="utf-8")
        print(f"{name} -> {veteran_name}")


if __name__ == "__main__":
    main()
