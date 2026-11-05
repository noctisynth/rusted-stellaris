"""Compiler regressions: prevent missing coverage and unsafe generated text."""

import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from localization import load_catalogs, render_ini, render_map, synchronize, SOURCE


class LocalizationTests(unittest.TestCase):
    def setUp(self):
        self.catalogs = {"zh": {"ship": "护卫舰"}, "en": {"ship": "Corvette"}}
        self.bindings = {"units/ship.ini::core::displayText": "ship"}

    def test_child_override_and_english_fallback(self):
        source = "[core]\ncopyFrom: parent.ini\nname: rsShip\ndisplayText: stale\ndisplayText_en: Parent\ndisplayText_zh: 父级\nmaxHp: 650\n"
        output, used = render_ini(source, "units/ship.ini", self.catalogs, self.bindings)
        self.assertIn("displayText: Corvette\ndisplayText_zh: 护卫舰\ndisplayText_en: Corvette\n", output)
        self.assertIn("copyFrom: parent.ini\nname: rsShip\n", output)
        self.assertIn("maxHp: 650\n", output)
        self.assertEqual(used, set(self.bindings))
        self.assertEqual(render_ini(output, "units/ship.ini", self.catalogs, self.bindings)[0], output)

    def test_new_text_cannot_bypass_catalog(self):
        with self.assertRaisesRegex(ValueError, "Uncatalogued"):
            render_ini("[action_build]\ntext: New button\n", "units/ship.ini", self.catalogs, self.bindings)
        with self.assertRaisesRegex(ValueError, "Uncatalogued"):
            render_ini("[action_build]\ntext_zh: 新按钮\n", "units/ship.ini", self.catalogs, self.bindings)

    def test_duplicate_fields_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate localized"):
            render_ini("[core]\ndisplayText: A\ndisplayText: B\n", "units/ship.ini", self.catalogs, self.bindings)

    def test_map_text_types_and_trigger_identifiers(self):
        text = '<map><objectgroup><object id="1" name="map_info"><properties><property name="introText" value="Old"/></properties></object><object id="2" name="stable-trigger" type="mapText"><properties><property name="text" value="Old"/><property name="globalMessage" value="Old"/><property name="activatedBy" value="capitalLost0"/></properties></object></objectgroup></map>'
        bindings = {f"maps/map.tmx::object:{i}::{key}": "ship" for i, key in ((1, "introText"), (2, "text"), (2, "globalMessage"))}
        output, used = render_map(text, "map.tmx", self.catalogs, bindings)
        self.assertEqual(used, set(bindings))
        tree = ET.fromstring(output)
        self.assertEqual(tree.find(".//object[@id='2']").get("name"), "stable-trigger")
        self.assertEqual(tree.find(".//property[@name='activatedBy']").get("value"), "capitalLost0")
        self.assertEqual(tree.find(".//property[@name='text_zh']").get("value"), "护卫舰")
        self.assertEqual(render_map(output, "map.tmx", self.catalogs, bindings)[0], output)
        with self.assertRaisesRegex(ValueError, "Uncatalogued map"):
            render_map(text, "map.tmx", self.catalogs, {})

    def test_metadata_uses_plain_bilingual_description(self):
        output, _ = render_ini("[mod]\ntitle: Rusted Stellaris\ndescription: Old\n", "mod-info.txt", self.catalogs, {"mod-info.txt::mod::description": "ship"})
        self.assertIn("description: 护卫舰 / Corvette\n", output)
        self.assertNotIn("description_", output)

    def test_catalog_validation_and_stale_output(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "locales").mkdir()
            (root / SOURCE / "units").mkdir(parents=True)
            paths = {lang: root / f"locales/{lang}.json" for lang in self.catalogs}
            for lang, path in paths.items():
                path.write_text(json.dumps(self.catalogs[lang]), encoding="utf-8")
            (root / "locales/bindings.json").write_text(json.dumps(self.bindings), encoding="utf-8")
            (root / SOURCE / "all-units.template").write_text("\n", encoding="utf-8")
            (root / SOURCE / "mod-info.txt").write_text("[mod]\n", encoding="utf-8")
            unit = root / SOURCE / "units/ship.ini"
            unit.write_text("[core]\ndisplayText: Old\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Stale localized"):
                synchronize(root)
            self.assertEqual(synchronize(root, write=True), (1, 1, 1))
            self.assertEqual(synchronize(root), (1, 1, 0))
            paths["en"].write_text('{"ship":""}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing translation"):
                load_catalogs(root)
            paths["en"].write_text('{"ship":"护卫舰"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "untranslated Chinese"):
                load_catalogs(root)
            paths["en"].write_text('{"ship":"%{self.playerName}"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "placeholders differ"):
                load_catalogs(root)
            paths["en"].write_text('{"ship":"a", "ship":"b"}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                load_catalogs(root)


if __name__ == "__main__":
    unittest.main()
