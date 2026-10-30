import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COLOR_DIR = ROOT / "assets" / "logos" / "color"


class ColorLogoManifestTest(unittest.TestCase):
    def test_color_logo_assets_are_present_and_match_their_formats(self):
        manifest = json.loads((COLOR_DIR / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_repository"], "rekryt/iplist")
        self.assertEqual(manifest["source_license"], "MIT")
        self.assertGreaterEqual(len(manifest["logos"]), 25)
        for slug, entry in manifest["logos"].items():
            with self.subTest(slug=slug):
                path = COLOR_DIR / entry["file"]
                self.assertTrue(path.is_file(), f"missing color icon: {entry['file']}")
                body = path.read_bytes()
                self.assertGreater(len(body), 0)
                self.assertLessEqual(len(body), 300_000)
                if entry["format"] == "png":
                    self.assertTrue(body.startswith(b"\x89PNG\r\n\x1a\n"))
                elif entry["format"] == "ico":
                    self.assertGreaterEqual(len(body), 6)
                    self.assertEqual(body[:4], b"\x00\x00\x01\x00")
                else:
                    self.fail(f"unsupported icon format: {entry['format']}")
                self.assertEqual(path.name.rsplit(".", 1)[0], slug)
                self.assertIn("rekryt/iplist", entry["source_url"])
                self.assertTrue(entry["source_path"].startswith("storage/icons/"))


if __name__ == "__main__":
    unittest.main()
