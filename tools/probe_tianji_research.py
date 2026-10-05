"""Probe periodic random research in a disposable Windows game copy.

Requires the built mod at mods/units/RustedStellarisDev. Only game directories
inside this repository's ignored work/ folder are accepted. The temporary test
building is removed even when the probe fails. Never use text debug
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
[core]
copyFrom: fleet_academy.ini
name: rsTianjiProbe
displayText: 天机研究所（技术原型）
defineUnitMemory: float roll
canNotBeDamaged: true

[hiddenAction_start]
autoTriggerOnEvent: completeAndActive
resetCustomTimer: true

[hiddenAction_attempt]
autoTrigger: if self.customTimer>2
resetCustomTimer: true
setUnitMemory: roll=rnd(0,1)
addResources: tianjiAttempts=1
alsoTriggerAction: failed, outcomeA, outcomeB, outcomeC

[hiddenAction_failed]
requireConditional: if memory.roll>=0.1
addResources: tianjiFailed=1

[hiddenAction_outcomeA]
requireConditional: if memory.roll<0.03333333
addResources: tianjiA=1
addGlobalTeamTags: rsProbeLostTechA

[hiddenAction_outcomeB]
requireConditional: if memory.roll>=0.03333333 and memory.roll<0.06666667
addResources: tianjiB=1
addGlobalTeamTags: rsProbeLostTechB

[hiddenAction_outcomeC]
requireConditional: if memory.roll>=0.06666667 and memory.roll<0.1
addResources: tianjiC=1
addGlobalTeamTags: rsProbeLostTechC

[global_resource_tianjiAttempts]
displayName: tianjiAttempts
hidden: true

[global_resource_tianjiFailed]
displayName: tianjiFailed
hidden: true

[global_resource_tianjiA]
displayName: tianjiA
hidden: true

[global_resource_tianjiB]
displayName: tianjiB
hidden: true

[global_resource_tianjiC]
displayName: tianjiC
hidden: true
"""


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, required=True)
    args = parser.parse_args()
    game = args.game_dir.resolve()
    work = (ROOT / "work").resolve()
    if not game.is_relative_to(work):
        parser.error("Use a disposable game copy inside the repository's work/ directory")
    unit = game / "mods/units/RustedStellarisDev/units/probe_tianji.ini"
    java = game / "jvm64/bin/java.exe"
    if not (unit.parent / "fleet_academy.ini").is_file() or not java.is_file():
        parser.error("Install the game runtime and built mod in the disposable copy first")
    original = unit.read_bytes() if unit.exists() else None
    if original is not None:
        parser.error("A previous probe action is still present; restore the sandbox first")
    run = work / ("tianji-probe-" + uuid4().hex[:12])
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

    snapshots = []

    def save(suffix):
        name = f"{run.name}-{suffix}"
        path = game / "saves" / (name + ".rwsave")
        send(f"root.saveGame('{name}')")
        wait_for(lambda log: path.is_file() and "Finished writing save" in log, "binary save")
        raw = raw_save(path)
        names, _ = unit_list(raw)
        assert names.count("rsTianjiProbe")==1
        values={}
        for suffix in ["Attempts","Failed","A","B","C"]:
            key=("g_tianji"+suffix).encode()
            hits=[]
            cursor=0
            while True:
                pos=raw.find(key,cursor)
                if pos<0:break
                cursor=pos+1
                if int.from_bytes(raw[pos-2:pos],"big")==len(key):
                    hits.append(unpack(">d",raw[pos+len(key):pos+len(key)+8])[0])
            values[suffix]=max(hits,default=0)
        if snapshots:
            assert values["Attempts"] > snapshots[-1]["Attempts"], "Research did not resume after loading"
            assert all(values[k]>=snapshots[-1][k] for k in values), "Counters lost on load"
        snapshots.append(values)
        print(name, values, flush=True)
        assert values["Attempts"]>0, values
        assert values["Attempts"]==sum(values[k] for k in ["Failed","A","B","C"]),values
        assert values["Failed"]>sum(values[k] for k in ["A","B","C"]),values
        if name.endswith("reloaded"):
            assert all(values[k]>0 for k in ["A","B","C"]),values
            assert all(("rsprobelosttech"+k.lower()).encode() in raw for k in ["A","B","C"])
        return path

    command = [str(java), "-Xmx1000M", "-Dfile.encoding=UTF-8", "-Djava.library.path=.",
               "-cp", "game-lib.jar;libs/*", "com.corrodinggames.rts.java.Main",
               "-width", "800", "-height", "600", "-debug", f"{port}:save-probe",
               "-debugscript", str(script)]
    proc = None
    try:
        unit.write_text(ACTION, encoding="utf-8")
        with stdout.open("wb") as out, stderr.open("wb") as err:
            proc = Popen(command, cwd=game, stdout=out, stderr=err, creationflags=CREATE_NO_WINDOW)
            wait_for(lambda log: "--- setRunning ---" in log, "map startup")
            sleep(3)
            send("debug.plainTextDebugSave(false)")
            sleep(1)
            send("debug.setTeamAllyGroup(1,0)")
            send("debug.setTeamAllyGroup(0,0)")
            send("debug.createUnit('rsTianjiProbe',100,1600,0,false)")
            send("debug.overrideDeltaSpeed(3)")
            sleep(18)
            first = save("initial")
            send(f"root.loadGame('{first.name}')")
            wait_for(lambda log: "--- Save file load complete ---" in log, "save loading")
            send("root.resumeNonMenu()")
            # Continue periodic research after loading.
            send("debug.overrideDeltaSpeed(3)")
            sleep(18)
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
        unit.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
