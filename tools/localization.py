"""Compile centrally managed translations into RW's native locale fields.

The checked-in INI/TMX files remain directly installable. Catalogs are the
authority; --check (the default) rejects missing coverage and stale output.
"""

from argparse import ArgumentParser
from collections import Counter
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("mod/rusted-stellaris")
LANGUAGES = ("zh", "en")
INI_FIELDS = {
    "displayText", "displayDescription", "displayName", "displayNameShort",
    "text", "description", "isLockedMessage", "isLockedAltMessage",
    "isLockedAlt2Message", "cannotPlaceMessage", "showMessageToPlayer",
    "showMessageToAllPlayers", "showMessageToAllEnemyPlayers",
    "showQuickWarLogToPlayer", "showQuickWarLogToAllPlayers",
}
PLACEHOLDER = re.compile(r"%\{[^}]+\}|\$\{[^}]+\}")
HAN = re.compile(r"[\u4e00-\u9fff]")
HEADER = "# Text is generated from locales/*.json; run tools/localization.py --write."


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"{path}: duplicate JSON key {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def load_catalogs(root=ROOT):
    catalogs = {lang: read_json(root / "locales" / f"{lang}.json") for lang in LANGUAGES}
    bindings = read_json(root / "locales/bindings.json")
    keys = set(catalogs["zh"])
    if any(set(catalog) != keys for catalog in catalogs.values()):
        raise ValueError("zh/en catalogs must have identical translation keys")
    if set(bindings.values()) != keys:
        raise ValueError("Every translation must be bound, and every binding must have a translation")
    for key in sorted(keys):
        for lang in LANGUAGES:
            value = catalogs[lang][key]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{lang}:{key}: missing translation")
            if any(char in value for char in "\r\n\0") or value.strip() != value:
                raise ValueError(f"{lang}:{key}: use literal \\n for line breaks; no surrounding whitespace")
            if lang == "en" and HAN.search(value):
                raise ValueError(f"en:{key}: untranslated Chinese in English text")
        if Counter(PLACEHOLDER.findall(catalogs["zh"][key])) != Counter(PLACEHOLDER.findall(catalogs["en"][key])):
            raise ValueError(f"{key}: runtime placeholders differ between languages")
    return catalogs, bindings


def ini_field(section, key, mod_info=False):
    if mod_info:
        return section == "mod" and key == "description"
    return key in INI_FIELDS


def render_ini(text, name, catalogs, bindings):
    """Return generated content and the bindings consumed; do not touch other keys."""
    lines, used, seen = [], set(), set()
    section = ""
    mod_info = name == "mod-info.txt"
    for raw in text.splitlines():
        if raw == HEADER:
            continue
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
        if not line.startswith(("#", ";")) and ":" in line:
            key = line.split(":", 1)[0].strip()
            base, _, lang = key.rpartition("_")
            if lang in LANGUAGES and ini_field(section, base, mod_info):
                if f"{name}::{section}::{base}" not in bindings:
                    raise ValueError(f"Uncatalogued player text: {name}::{section}::{key}")
                continue  # Language variants are regenerated from the catalog.
            if ini_field(section, key, mod_info):
                target = f"{name}::{section}::{key}"
                if target in seen:
                    raise ValueError(f"Duplicate localized field: {target}")
                seen.add(target)
                if target not in bindings:
                    raise ValueError(f"Uncatalogued player text: {target}")
                message = bindings[target]
                used.add(target)
                if mod_info:
                    # mod-info description is a plain string, not LocaleString.
                    lines.append(f"{key}: {catalogs['zh'][message]} / {catalogs['en'][message]}")
                else:
                    # forceEnglish uses Locale.ROOT (empty code), so the
                    # unsuffixed fallback must also be English.
                    lines.append(f"{key}: {catalogs['en'][message]}")
                    lines.extend(f"{key}_{lang}: {catalogs[lang][message]}" for lang in LANGUAGES)
                continue
        lines.append(raw)
    if used:
        lines.insert(0, HEADER)
    return "\n".join(lines) + "\n", used


def map_fields(root):
    """Object IDs address text; object names and gameplay properties stay intact."""
    for obj in root.findall(".//objectgroup/object"):
        props = obj.find("properties")
        if props is None:
            continue
        keys = {"globalMessage"}
        if obj.get("name", "").strip().lower() == "map_info":
            keys.add("introText")
        if obj.get("type", "").lower() == "maptext":
            keys.add("text")
        yield obj, props, keys


def render_map(text, name, catalogs, bindings):
    tree, used = ET.fromstring(text), set()
    for obj, props, keys in map_fields(tree):
        for prop in list(props):
            key = prop.get("name", "")
            base, _, lang = key.rpartition("_")
            if lang in LANGUAGES and base in keys:
                target = f"maps/{name}::object:{obj.attrib['id']}::{base}"
                if target not in bindings:
                    raise ValueError(f"Uncatalogued map text: {target}")
            if key in keys:
                target = f"maps/{name}::object:{obj.attrib['id']}::{key}"
                if target in used:
                    raise ValueError(f"Duplicate localized map field: {target}")
                if target not in bindings:
                    raise ValueError(f"Uncatalogued map text: {target}")
                message = bindings[target]
                used.add(target)
                prop.text = None
                prop.set("value", catalogs["en"][message])
                for lang in LANGUAGES:
                    localized = [p for p in props if p.get("name") == f"{key}_{lang}"]
                    for old in localized:
                        props.remove(old)
                    ET.SubElement(props, "property", name=f"{key}_{lang}", value=catalogs[lang][message])
    if not used:
        return text, used
    ET.indent(tree)
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(tree, encoding="unicode") + "\n", used


def synchronize(root=ROOT, *, write=False):
    catalogs, bindings = load_catalogs(root)
    used, changed = set(), []
    files = sorted((root / SOURCE).rglob("*.ini"))
    files += [root / SOURCE / "all-units.template", root / SOURCE / "mod-info.txt"]
    files += sorted((root / "maps").glob("*.tmx"))
    for path in files:
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".tmx":
            output, consumed = render_map(text, path.name, catalogs, bindings)
        else:
            output, consumed = render_ini(text, path.relative_to(root / SOURCE).as_posix(), catalogs, bindings)
        used.update(consumed)
        if text != output:
            changed.append((path, output))
    if missing := set(bindings) - used:
        raise ValueError(f"Bindings point to missing text fields: {sorted(missing)}")
    # Validate everything before writing any output.
    if write:
        for path, output in changed:
            path.write_text(output, encoding="utf-8", newline="\n")
    elif changed:
        raise ValueError("Stale localized files; run tools/localization.py --write: " + ", ".join(str(p.relative_to(root)) for p, _ in changed))
    return len(catalogs["zh"]), len(used), len(changed)


def main():
    parser = ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Update native locale fields from the catalogs")
    mode.add_argument("--check", action="store_true", help="Check completeness and generated output (default)")
    args = parser.parse_args()
    try:
        messages, targets, changed = synchronize(write=args.write)
    except (ValueError, KeyError) as error:
        parser.exit(1, f"Localization error: {error}\n")
    print(f"Localization: {messages} messages, {targets} text fields, zh/en complete; {changed} files updated")


if __name__ == "__main__":
    main()
