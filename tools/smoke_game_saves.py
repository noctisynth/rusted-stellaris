"""Check dynamic-stat save/load/resave in a disposable Windows game copy.

Requires the built mod at mods/units/RustedStellarisDev. Only game directories
inside this repository's ignored work/ folder are accepted. The temporary
corvette action is restored even when the probe fails. Never use text debug
saves for persistence checks: RW 1.15's text writer cannot serialize doubles.
"""

from argparse import ArgumentParser
from pathlib import Path
from struct import pack, unpack
from subprocess import CREATE_NO_WINDOW, Popen, TimeoutExpired
from time import monotonic, sleep
from uuid import uuid4
import socket

from inspect_save_units import raw_save, unit_list


ROOT = Path(__file__).resolve().parents[1]
ACTION = """
[hiddenAction_saveRegressionProbe]
autoTrigger: if not self.tags(includes='rsSaveProbeDone')
setUnitStats: maxHp+=100, shootDamageMultiplier+=0.1
temporarilyAddTags: rsSaveProbeDone
"""


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, required=True)
    args = parser.parse_args()
    game = args.game_dir.resolve()
    work = (ROOT / "work").resolve()
    if not game.is_relative_to(work):
        parser.error("Use a disposable game copy inside the repository's work/ directory")
    unit = game / "mods/units/RustedStellarisDev/units/corvette.ini"
    java = game / "jvm64/bin/java.exe"
    if not unit.is_file() or not java.is_file():
        parser.error("Install the game runtime and built mod in the disposable copy first")
    original = unit.read_bytes()
    if b"saveRegressionProbe" in original:
        parser.error("A previous probe action is still present; restore the sandbox first")
    run = work / ("save-smoke-" + uuid4().hex[:12])
    run.mkdir()
    stdout, stderr = run / "stdout.log", run / "stderr.log"
    target = "/SD/mods/units/RustedStellarisDev/[p2]Twin_Chokepoints.tmx"
    script = run / "start.debug"
    script.write_text(f"root.open('levelOptions.rml', '{target}')\n"
                      f"root.loadConfigAndStartNew('{target}')\n", encoding="utf-8")
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]

    def send(command):
        with socket.create_connection(("127.0.0.1", port), timeout=4) as channel:
            channel.settimeout(15)
            channel.sendall(("script " + command + "\n").encode())
            reply = channel.recv(2048)
            if reply.strip() != b"done":
                raise RuntimeError(f"Unexpected debug reply: {reply!r}")
        # 'done' acknowledges the script; it does NOT establish save success.

    def wait_for(predicate, description, seconds=45):
        deadline = monotonic() + seconds
        while monotonic() < deadline:
            if proc.poll() is not None:
                raise RuntimeError(f"Game exited while waiting for {description}; see {run}")
            logs = stdout.read_text(encoding="utf-8", errors="replace")
            errors = stderr.read_text(encoding="utf-8", errors="replace")
            if "Exception" in errors or "Error saving game" in logs or "onGameCrash:" in logs:
                raise RuntimeError(f"Game reported an error; see {run}")
            if predicate(logs):
                return
            sleep(.2)
        raise TimeoutError(f"Timed out waiting for {description}; see {run}")

    def save(suffix):
        name = f"{run.name}-{suffix}"
        path = game / "saves" / (name + ".rwsave")
        send(f"root.saveGame('{name}')")
        wait_for(lambda log: path.is_file() and "Finished writing save" in log, "binary save")
        raw = raw_save(path)
        names, _ = unit_list(raw)
        count = names.count("rsCorvette")
        # RW 1.15 stat-diff records: field ID (short), value and default (doubles).
        # IDs 3 and 11 are maxHp and shootDamageMultiplier, respectively.
        hp_count = raw.count(pack(">hdd", 3, 750., 650.))
        damage = unpack(">f", pack(">f", 1.1))[0]
        damage_count = raw.count(pack(">hdd", 11, damage, 1.))
        if count != 8 or hp_count != count or damage_count != count:
            raise AssertionError(f"Unexpected probe stats: units={count}, hp={hp_count}, damage={damage_count}")
        if raw.count(b"rssaveprobedone") != count:
            raise AssertionError("Training guard did not persist on all eight corvettes")
        print(f"{suffix}: {count} unchanged rsCorvette IDs, maxHp=750, damage=1.1, guard preserved", flush=True)
        return path

    command = [str(java), "-Xmx1000M", "-Dfile.encoding=UTF-8", "-Djava.library.path=.",
               "-cp", "game-lib.jar;libs/*", "com.corrodinggames.rts.java.Main",
               "-width", "800", "-height", "600", "-debug", f"{port}:save-probe",
               "-debugscript", str(script)]
    proc = None
    try:
        unit.write_bytes(original + ACTION.encode("utf-8"))
        with stdout.open("wb") as out, stderr.open("wb") as err:
            proc = Popen(command, cwd=game, stdout=out, stderr=err, creationflags=CREATE_NO_WINDOW)
            wait_for(lambda log: "--- setRunning ---" in log, "map startup")
            sleep(3)
            send("debug.plainTextDebugSave(false)")
            first = save("initial")
            send(f"root.loadGame('{first.name}')")
            wait_for(lambda log: "--- Save file load complete ---" in log, "save loading")
            send("root.resumeNonMenu()")
            # Let auto actions execute again: an unsaved guard would stack buffs.
            sleep(5)
            save("reloaded")
            print(f"PASS: binary save/load/resave; evidence: {run}", flush=True)
    finally:
        if proc is not None:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=5)
            except TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        unit.write_bytes(original)


if __name__ == "__main__":
    main()
