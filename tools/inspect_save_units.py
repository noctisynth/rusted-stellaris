"""Inspect custom-unit IDs in a Rusted Warfare 1.15 binary save.

This reads the save's compressed block and validates an object-list candidate
against increasing game-object IDs. Custom units and the built-in type-2 objects
observed in project test maps are supported; this is not a general save decoder.
"""

from argparse import ArgumentParser
from collections import Counter
from gzip import decompress
from pathlib import Path


def raw_save(path: Path) -> bytes:
    data = path.read_bytes()
    start = data.find(b"\x1f\x8b")
    if start < 4:
        raise ValueError("save has no length-prefixed gzip block")
    length = int.from_bytes(data[start - 4:start], "big")
    return decompress(data[start:start + length])


def unit_names(raw: bytes) -> list[str]:
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
            return names
    raise ValueError("no all-custom sequential unit list found")


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("save", type=Path)
    parser.add_argument("--ordered", action="store_true", help="show units in save order")
    args = parser.parse_args()
    names = unit_names(raw_save(args.save))
    print(f"{len(names)} game objects in {args.save}")
    if args.ordered:
        for number, name in enumerate(names, 1):
            print(f"{number:3}: {name}")
    else:
        for name, count in sorted(Counter(names).items()):
            print(f"{name}: {count}")


if __name__ == "__main__":
    main()
