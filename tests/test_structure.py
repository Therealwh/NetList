import tempfile
import unittest
from pathlib import Path

from scripts.netlist_data.check_structure import violations


class StructureTest(unittest.TestCase):
    def test_structure_rejects_site_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "public").mkdir()
            (root / "public" / "index.php").write_text("<?php echo 1;")
            (root / "templates").mkdir()
            (root / "templates" / "base.html").write_text("<html></html>")
            (root / "assets").mkdir()
            (root / "assets" / "app.js").write_text("alert(1)")
            found = violations(root)
            self.assertTrue(any("index.php" in v for v in found))
            self.assertTrue(any("base.html" in v for v in found))
            self.assertTrue(any("app.js" in v for v in found))

    def test_structure_rejects_dotenv_secrets_and_archives(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sources").mkdir()
            (root / "sources" / ".env").write_text("TOKEN=1")
            (root / "state.sqlite").write_bytes(b"")
            (root / "dump.zip").write_bytes(b"")
            (root / "private.pem").write_text("PRIVATE KEY")
            found = violations(root)
            self.assertTrue(any(".env" in v for v in found))
            self.assertTrue(any("sqlite" in v for v in found))
            self.assertTrue(any("dump.zip" in v for v in found))
            self.assertTrue(any("private.pem" in v for v in found))

    def test_allowed_layout_and_bilingual_readmes_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for item in ("scripts", "tests", "sources/seed/global",
                         "schemas", "state", "services", "collections",
                         "common", "assets/logos", ".github/workflows"):
                (root / item).mkdir(parents=True, exist_ok=True)
            (root / "catalog.json").write_text("{}")
            (root / "README.md").write_text("# NetList")
            (root / "README_EN.md").write_text("# NetList")
            (root / "README_RU.md").write_text("# NetList")
            (root / ".gitignore").write_text("")
            (root / ".gitattributes").write_text("")
            (root / "scripts" / "netlist_data").mkdir(parents=True)
            (root / "scripts" / "netlist_data" / "build.py").write_text("x")
            self.assertEqual(violations(root), [])


if __name__ == "__main__":
    unittest.main()
