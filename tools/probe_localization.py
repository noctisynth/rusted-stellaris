"""Verify localized text with the installed RW 1.15 Java parsers (read only)."""

from argparse import ArgumentParser
from base64 import b64encode
from pathlib import Path
import os
import subprocess
from uuid import uuid4

from localization import ROOT, SOURCE, load_catalogs, synchronize, render_map


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, required=True)
    args = parser.parse_args()
    game = args.game_dir.resolve()
    java, javac = (game / "jvm64/bin" / name for name in ("java.exe", "javac.exe"))
    if not java.is_file() or not javac.is_file():
        parser.error("The game directory must contain the bundled JDK")
    synchronize()
    catalogs, bindings = load_catalogs()
    run = ROOT / "work" / ("i18n-native-" + uuid4().hex[:10])
    run.mkdir(parents=True)
    checks = []
    for target, message in bindings.items():
        name, section, key = target.split("::")
        if name == "mod-info.txt" or name.startswith("maps/"):
            continue
        for lang in ("zh", "en", "", "fr"):
            expected = catalogs["zh" if lang == "zh" else "en"][message].replace("\\n", "\n")
            checks.append("\t".join((str(ROOT / SOURCE / name), section, key, lang,
                                      b64encode(expected.encode()).decode())))
    (run / "checks.tsv").write_text("\n".join(checks) + "\n", encoding="utf-8")
    fixture = '''<map><objectgroup name="Triggers">
<object id="1" name="map_info" x="0" y="0"><properties><property name="introText" value="Map text"/></properties></object>
<object id="2" type="basic" x="0" y="0"><properties><property name="globalMessage" value="Map text"/></properties></object>
<object id="3" type="mapText" x="0" y="0"><properties><property name="text" value="Map text"/></properties></object>
</objectgroup></map>'''
    targets = {f"maps/probe.tmx::object:{i}::{key}": "probe" for i, key in enumerate(("introText", "globalMessage", "text"), 1)}
    output, _ = render_map(fixture, "probe.tmx", {"zh": {"probe": "地图文本"}, "en": {"probe": "Map text"}}, targets)
    # Java receives just the objectgroup to exercise RW's constructor.
    from xml.etree import ElementTree as ET
    ET.ElementTree(ET.fromstring(output).find("objectgroup")).write(run / "map.xml", encoding="utf-8")
    classpath = os.pathsep.join((str(game / "game-lib.jar"), str(game / "libs/*")))
    common = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    subprocess.run([str(javac), "-encoding", "UTF-8", "-cp", classpath, "-d", str(run),
                    str(ROOT / "tools/probes/LocalizationProbe.java")], check=True, **common)
    result = subprocess.run([str(java), "-Dfile.encoding=UTF-8", "-cp", os.pathsep.join((str(run), classpath)),
                             "LocalizationProbe", str(run / "checks.tsv"), str(run / "map.xml")],
                            capture_output=True, text=True, encoding="utf-8", **common)
    (run / "stdout.log").write_text(result.stdout, encoding="utf-8")
    (run / "stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"Native locale check failed: {result.stderr[-2500:]}\nEvidence: {run}")
    print(result.stdout.splitlines()[-1])
    print(f"Evidence: {run}")


if __name__ == "__main__":
    main()
