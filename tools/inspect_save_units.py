"""Inspect custom-unit IDs in a Rusted Warfare 1.15 binary save.

This reads the save's compressed block and validates an object-list candidate
against increasing game-object IDs. Custom units and the built-in type-2 objects
observed in project test maps are supported; this is not a general save decoder.
The optional position view marks a team as unknown when its serialized layout
differs from the common custom-unit layout.
"""

from argparse import ArgumentParser
from collections import Counter
from gzip import decompress
from pathlib import Path
import re
from struct import unpack


def raw_save(path: Path) -> bytes:
    data = path.read_bytes()
    start = data.find(b"\x1f\x8b")
    if start < 4:
        raise ValueError("save has no length-prefixed gzip block")
    length = int.from_bytes(data[start - 4:start], "big")
    return decompress(data[start:start + length])


def unit_list(raw: bytes) -> tuple[list[str], int]:
    for start in range(len(raw) - 15):
        count = int.from_bytes(raw[start:start + 4], "big")
        if not 1 <= count <= 10000 or raw[start + 4] != 3:
            continue
        pos = start + 4
        names = []
        last_id = 0
        for number in range(1, count + 1):
            if pos + 10 > len(raw):
                break
            if raw[pos] == 3:
                size = int.from_bytes(raw[pos + 1:pos + 3], "big")
                name = raw[pos + 3:pos + 3 + size]
                if not 3 <= size <= 100 or not name.startswith(b"rs") or not name.isascii():
                    break
                pos += 3 + size
                label = name.decode("ascii")
            elif raw[pos] == 2:
                label = f"builtin:{raw[pos + 1]}"
                pos += 2
            else:
                break
            object_id = int.from_bytes(raw[pos:pos + 8], "big")
            if object_id <= last_id:
                break
            last_id = object_id
            pos += 8
            names.append(label)
        if len(names) == count:
            return names, pos
    raise ValueError("no supported ordered game-object list found")


def unit_positions(raw: bytes, names: list[str], start: int) -> list[tuple[int | None, float, float]]:
    """Decode coordinates and common-layout team IDs for custom-only 1.15 maps."""
    if any(not name.startswith("rs") for name in names):
        raise ValueError("position decoding requires custom units only")
    markers = list(re.finditer(
        rb"\xff\xfe\x00\x00(?:\x3f\x80\x00\x00|\x00\x00\x00\x00)", raw[start:]
    ))
    if len(markers) != len(names):
        raise ValueError(f"expected {len(names)} coordinate records, found {len(markers)}")
    result = []
    for marker in markers:
        pos = start + marker.start()
        team = raw[pos - 227]
        team = team if team < 128 else team - 256
        x, y = unpack(">ff", raw[pos + 8:pos + 16])
        if not 0 <= x <= 10000 or not 0 <= y <= 10000:
            raise ValueError("coordinate record failed bounds validation")
        result.append((team if -1 <= team <= 9 else None, x, y))
    return result


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("save", type=Path)
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--ordered", action="store_true", help="show units in save order")
    options.add_argument("--positions", action="store_true", help="show custom-unit teams and coordinates")
    args = parser.parse_args()
    raw = raw_save(args.save)
    names, list_end = unit_list(raw)
    print(f"{len(names)} game objects in {args.save}")
    if args.positions:
        try:
            positions = unit_positions(raw, names, list_end)
        except ValueError as error:
            parser.error(str(error))
        for number, (name, (team, x, y)) in enumerate(zip(names, positions), 1):
            team_label = str(team) if team is not None else "?"
            print(f"{number:3}: team={team_label:>2} x={x:7.1f} y={y:7.1f} {name}")
    elif args.ordered:
        for number, name in enumerate(names, 1):
            print(f"{number:3}: {name}")
    else:
        for name, count in sorted(Counter(names).items()):
            print(f"{name}: {count}")


if __name__ == "__main__":
    main()
