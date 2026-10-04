"""Verify actual in-game playback and rotation in a disposable Windows game copy.

Install the built mod under mods/units/RustedStellarisDev first. Use an isolated
game directory: this launches the game, opens a local debug port, and saves a
probe game. The process and port are closed on completion. Original music may
play in the menu, but must not return after the mod's exclusive playlist starts.
"""
from argparse import ArgumentParser
from pathlib import Path
from subprocess import CREATE_NO_WINDOW, Popen, TimeoutExpired
from time import monotonic, sleep
import re
import socket

from music.build_support import ROOT, filename, tracks


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--skip-natural", action="store_true", help="Only test explicit next-track rotation")
    args = parser.parse_args()
    game = args.game_dir.resolve()
    if not (game / "jvm64/bin/java.exe").is_file():
        parser.error("No bundled Java runtime in the test game directory")
    expected = {filename(t) for t in tracks()}
    music = game / "mods/units/RustedStellarisDev/music"
    if not all((music / name).is_file() for name in expected):
        parser.error("Extract the built mod, including all four OGG files, before this test")
    work = ROOT / "work"
    script = work / "music-smoke.debug"
    stdout = work / "music-smoke.stdout.log"
    stderr = work / "music-smoke.stderr.log"
    target = "/SD/mods/units/RustedStellarisDev/[p2]Twin_Chokepoints.tmx"
    script.write_text(f"root.open('levelOptions.rml', '{target}')\n"
                      f"root.loadConfigAndStartNew('{target}')\n", encoding="utf-8")
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]

    def send(command):
        with socket.create_connection(("127.0.0.1", port), timeout=4) as channel:
            channel.settimeout(8)
            channel.sendall(("script " + command + "\n").encode())
            reply = channel.recv(2048)
            if b"crash" in reply.lower() or b"error" in reply.lower():
                raise RuntimeError(repr(reply))

    command = [str(game / "jvm64/bin/java.exe"), "-Xmx1000M", "-Dfile.encoding=UTF-8",
               "-Djava.library.path=.", "-cp", "game-lib.jar;libs/*",
               "com.corrodinggames.rts.java.Main", "-width", "800", "-height", "600",
               "-debug", f"{port}:music-probe", "-debugscript", str(script)]
    with stdout.open("wb") as out, stderr.open("wb") as err:
        proc = Popen(command, cwd=game, stdout=out, stderr=err, creationflags=CREATE_NO_WINDOW)
        try:
            def state():
                text = stdout.read_text(encoding="utf-8", errors="replace")
                for message in ("onGameCrash:", "Failed to load music track", "Failed to play music track", "Music system crashed"):
                    if message in text:
                        raise RuntimeError(f"{message}; inspect {stdout}")
                if proc.poll() is not None:
                    raise RuntimeError("Game exited before playback checks completed")
                played = re.findall(r"Now playing:([^\r\n]+)", text)
                exclusive = next((i for i, p in enumerate(played) if "/RustedStellarisDev/music/" in p), len(played))
                sequence = played[exclusive:]
                if any(Path(p).name not in expected or "/RustedStellarisDev/music/" not in p for p in sequence):
                    raise RuntimeError("A non-mod track played after exclusive playback began")
                return text, sequence

            deadline = monotonic() + 55
            while monotonic() < deadline:
                text, sequence = state()
                if sequence:
                    break
                sleep(.25)
            else:
                raise TimeoutError("Mod music did not begin after map load")
            if not all(f"Found music track: {name}" in text for name in expected):
                raise RuntimeError("The game did not discover all four tracks")
            print("Exclusive music began: " + Path(sequence[-1]).name, flush=True)
            for attempt in range(10):
                if {Path(p).name for p in sequence} == expected:
                    break
                before = len(sequence)
                send("root.playNextMusicTrack()")
                deadline = monotonic() + 12
                while monotonic() < deadline:
                    _, sequence = state()
                    if len(sequence) > before:
                        print("Played: " + Path(sequence[-1]).name, flush=True)
                        break
                    sleep(.25)
                else:
                    raise TimeoutError("Next-track request did not produce playback")
                sleep(1)
            else:
                raise RuntimeError("Could not play every bundled track")
            print("All four tracks played without returning to vanilla music", flush=True)
            if not args.skip_natural:
                before = len(sequence)
                deadline = monotonic() + max(t["seconds"] for t in tracks()) + 25
                while monotonic() < deadline:
                    _, sequence = state()
                    if len(sequence) > before:
                        print("Natural end-of-track transition: " + Path(sequence[-1]).name, flush=True)
                        break
                    sleep(.5)
                else:
                    raise TimeoutError("No natural next track after the song should have ended")
            send("root.saveGame('music-playback-probe')")
        finally:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=5)
            except TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


if __name__ == "__main__":
    main()
