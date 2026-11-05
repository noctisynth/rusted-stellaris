"""Run a controlled zh/en build-combat-victory regression in a disposable game.

The probe queues a Corvette in a Shipyard-derived factory, then lets its normal
weapon destroy a one-HP unarmed enemy building. This tests the game lifecycle,
not balance or a normal economic campaign. No production units are modified.
"""

from argparse import ArgumentParser
from base64 import b64encode
from gzip import compress
from pathlib import Path
from struct import pack
import re
import socket
import subprocess
from subprocess import CREATE_NO_WINDOW, Popen, TimeoutExpired
from time import monotonic, sleep
from uuid import uuid4
from xml.etree import ElementTree as ET

from inspect_save_units import raw_save, unit_list
from localization import ROOT

FACTORY = """[core]
copyFrom: shipyard.ini
name: rsI18nFactoryProbe
tags: rsCapital
canNotBeDamaged: true
[hiddenAction_probeQueue]
autoTrigger: if self.customTimer>8 and not self.hasFlag(id=19)
addResources: setFlag=19
alsoQueueAction: probeBuild
[action_probeBuild]
text: Build Corvette
text_zh: 建造护卫舰
text_en: Build Corvette
price: 0
buildSpeed: 4s
produceUnits: rsCorvette
showMessageToPlayer: Ship construction complete
showMessageToPlayer_zh: 舰船建造完成
showMessageToPlayer_en: Ship construction complete
"""
TARGET = """[core]
copyFrom: repair_base.ini
name: rsI18nTargetProbe
tags: rsCapital
maxHp: 1
autoRepair: false
canRepairBuildings: false
canRepairUnits: false
[hiddenAction_probeDeath]
autoTriggerOnEvent: destroyed
addGlobalTeamTags: rsI18nTargetDestroyed
"""


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", required=True, type=Path)
    args = parser.parse_args()
    game = args.game_dir.resolve()
    if not game.is_relative_to((ROOT / "work").resolve()):
        parser.error("Use a disposable game copy inside the repository's work/ directory")
    mod = game / "mods/units/RustedStellarisDev"
    helpers = {mod / "units/probe_i18n_factory.ini": FACTORY,
               mod / "units/probe_i18n_target.ini": TARGET}
    map_path = mod / "I18n_Regression.tmx"
    if any(p.exists() for p in (*helpers, map_path)):
        parser.error("A previous probe exists; restore the disposable copy first")
    run = ROOT / "work" / ("i18n-match-" + uuid4().hex[:10])
    run.mkdir()
    subprocess.run([str(game / "jvm64/bin/javac.exe"), "-encoding", "UTF-8", "-d", str(run),
                    str(ROOT / "tools/probes/LocalizationGameProbe.java")], check=True, creationflags=CREATE_NO_WINDOW)
    proc = None
    try:
        for path, text in helpers.items():
            path.write_text(text, encoding="utf-8")
        tree = ET.parse(ROOT / "maps/[p2]Twin_Chokepoints.tmx")
        ET.SubElement(tree.find(".//object[@name='map_info']/properties"), "property",
                      name="winCondition", value="allUnitsAndBuildings")
        tileset = tree.find("./tileset[@firstgid='6']")
        for index, name in enumerate(("rsI18nFactoryProbe", "rsI18nTargetProbe")):
            for prop in tileset.find(f"tile[@id='{index}']/properties"):
                if prop.get("name") == "unit":
                    prop.set("value", name)
                elif prop.get("name") == "team":
                    prop.set("value", str(index))
        values = [0] * 10800
        values[45 * 120 + 50] = 6
        values[45 * 120 + 57] = 7
        tree.find("./layer[@name='Units']/data").text = b64encode(compress(pack("<10800I", *values))).decode()
        tree.write(map_path, encoding="utf-8", xml_declaration=True)
        for lang in ("en", "zh"):
            stdout, stderr = run / f"{lang}.stdout.log", run / f"{lang}.stderr.log"
            with socket.socket() as reserved:
                reserved.bind(("127.0.0.1", 0))
                port = reserved.getsockname()[1]
            target = "/SD/mods/units/RustedStellarisDev/I18n_Regression.tmx"
            script = run / f"{lang}.debug"
            script.write_text(f"root.open('levelOptions.rml', '{target}')\nroot.loadConfigAndStartNew('{target}')\n", encoding="utf-8")
            prefs = game / "preferences.ini"
            settings = prefs.read_text(encoding="utf-8")
            settings = re.sub(r"numIncompleteLoadAttempts:\d+", "numIncompleteLoadAttempts:0", settings)
            settings = re.sub(r"numLoadsSinceRunningGameOrNormalExit:\d+", "numLoadsSinceRunningGameOrNormalExit:0", settings)
            prefs.write_text(settings, encoding="utf-8")

            def command(code, *, function=False):
                with socket.create_connection(("127.0.0.1", port), timeout=4) as sock:
                    sock.settimeout(10)
                    sock.sendall((("function " if function else "script ") + code + "\n").encode())
                    result = sock.recv(4096)
                    if not function and result.strip() != b"done":
                        raise RuntimeError(f"Script failed: {result!r}")
                    return result

            def wait_for(predicate, label, timeout=35):
                deadline = monotonic() + timeout
                while monotonic() < deadline:
                    log = stdout.read_text(encoding="utf-8", errors="replace")
                    if proc.poll() is not None or "Error loading map:" in log or "onGameCrash:" in log:
                        raise RuntimeError(f"{lang}: failed while waiting for {label}; see {run}")
                    if predicate(log):
                        return
                    sleep(.25)
                raise TimeoutError(f"{lang}: timed out waiting for {label}; see {run}")

            def save(label):
                name = f"{run.name}-{lang}-{label}"
                path = game / "saves" / f"{name}.rwsave"
                command(f"root.saveGame('{name}')")
                wait_for(lambda log: path.exists() and log.count("Finished writing save") >= (1 if label == "before" else 2), label)
                raw = raw_save(path)
                return unit_list(raw)[0], raw

            java_args = [str(game / "jvm64/bin/java.exe"), "-Xmx1000M", "-Dfile.encoding=UTF-8",
                         "-Djava.library.path=.", "-cp", f"{run};game-lib.jar;libs/*",
                         "LocalizationGameProbe", "-lang", lang,
                         "-width", "800", "-height", "600", "-debug", f"{port}:i18n",
                         "-debugscript", str(script)]
            with stdout.open("wb") as out, stderr.open("wb") as err:
                proc = Popen(java_args, cwd=game, stdout=out, stderr=err, creationflags=CREATE_NO_WINDOW)
                try:
                    wait_for(lambda log: f"Mapfile: mods/units/RustedStellarisDev/{map_path.name}" in log and
                             "--- setRunning ---" in log.split(f"Mapfile: mods/units/RustedStellarisDev/{map_path.name}", 1)[1], "map startup")
                    command("debug.plainTextDebugSave(false)")
                    before, before_raw = save("before")
                    assert "rsCorvette" not in before and "rsI18nTargetProbe" in before, before
                    assert b"rsi18ntargetdestroyed" not in before_raw
                    assert "I18N_ENGINE_VICTORY" not in stdout.read_text(encoding="utf-8", errors="replace")
                    # Debug.isTeamInVictory reads a multiplayer team flag, not
                    # the single-player victory screen flag set by f.g.G().
                    wait_for(lambda log: "I18N_ENGINE_VICTORY" in log, "combat victory", 35)
                    after, after_raw = save("after")
                    # Destroyed buildings can remain serialized as wrecks.
                    assert after.count("rsCorvette") == 1 and b"rsi18ntargetdestroyed" in after_raw, after
                    assert "Exception" not in stderr.read_text(encoding="utf-8", errors="replace")
                    print(f"{lang}: queued and built 1 Corvette, destroyed enemy target, player victory confirmed", flush=True)
                finally:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except TimeoutExpired:
                        proc.kill()
                        proc.wait(timeout=5)
        print(f"PASS controlled build/combat/full-match regression; evidence: {run}")
    finally:
        if proc is not None and proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)
        for path in (*helpers, map_path):
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
