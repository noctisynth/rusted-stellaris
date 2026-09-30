"""Load each bundled map in Rusted Warfare 1.15 and verify map parsing.

Run on Windows with --game-dir pointing to the local Rusted Warfare install.
The source mod must already be installed in mods/units/RustedStellarisDev.
"""

from argparse import ArgumentParser
from pathlib import Path
from subprocess import CREATE_NO_WINDOW, Popen, TimeoutExpired
from time import monotonic, sleep


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
MAPS = (
    ("[p2]Twin_Chokepoints.tmx", 120, 90, 16),
    ("[p4]Three_Arms.tmx", 140, 140, 30),
    ("[p8]Shattered_Galaxy.tmx", 180, 180, 60),
)


def check_map(game_dir: Path, name: str, width: int, height: int, count: int, timeout: float) -> None:
    stem = name.removesuffix(".tmx").replace("[", "").replace("]", "")
    script = WORK / f"smoke-{stem}.debug"
    stdout = WORK / f"smoke-{stem}.stdout.log"
    stderr = WORK / f"smoke-{stem}.stderr.log"
    map_path = f"/SD/mods/units/RustedStellarisDev/{name}"
    script.write_text(
        f"root.open('levelOptions.rml', '{map_path}')\n"
        f"root.loadConfigAndStartNew('{map_path}')\n",
        encoding="utf-8",
    )
    args = [
        str(game_dir / "jvm64" / "bin" / "java.exe"),
        "-Xmx1000M",
        "-Dfile.encoding=UTF-8",
        "-Djava.library.path=.",
        "-cp",
        "game-lib.jar;libs/*",
        "com.corrodinggames.rts.java.Main",
        "-width",
        "800",
        "-height",
        "600",
        "-debugscript",
        str(script),
    ]
    with stdout.open("wb") as out, stderr.open("wb") as err:
        proc = Popen(args, cwd=game_dir, stdout=out, stderr=err, creationflags=CREATE_NO_WINDOW)
        try:
            deadline = monotonic() + timeout
            while monotonic() < deadline:
                log = stdout.read_text(encoding="utf-8", errors="replace")
                if "Error loading map:" in log or "onGameCrash:" in log:
                    raise RuntimeError(f"{name}: map error; inspect {stdout}")
                if (
                    f"Mapfile: mods/units/RustedStellarisDev/{name}" in log
                    and f"Map size: {width}, {height}" in log
                    and f"there are {count} units on this map" in log
                    and "--- setRunning ---" in log.split(f"Mapfile: mods/units/RustedStellarisDev/{name}", 1)[1]
                ):
                    print(f"{name}: loaded {width}x{height}, {count} units")
                    return
                if proc.poll() is not None:
                    raise RuntimeError(f"{name}: game exited before map loaded; inspect {stdout} and {stderr}")
                sleep(0.25)
            raise TimeoutError(f"{name}: no successful load within {timeout}s; inspect {stdout} and {stderr}")
        finally:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=5)
            except TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", required=True, type=Path)
    parser.add_argument("--timeout", type=float, default=25)
    args = parser.parse_args()
    game_dir = args.game_dir.resolve()
    if not (game_dir / "jvm64" / "bin" / "java.exe").is_file():
        parser.error("game directory has no bundled Java runtime")
    if not (game_dir / "mods" / "units" / "RustedStellarisDev").is_dir():
        parser.error("install the development mod before running this check")
    WORK.mkdir(exist_ok=True)
    for entry in MAPS:
        check_map(game_dir, *entry, args.timeout)


if __name__ == "__main__":
    main()
