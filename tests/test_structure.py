import tempfile
import unittest
from pathlib import Path

from scripts.netlist_data.check_structure import violations


class StructureTest(unittest.TestCase):
    def test_structure_rejects_site_files(self):
        # Review Focus #4
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "public").mkdir()
            (root / "public" / "index.php").write_text("<?php echo 1;")
            (root / "templates").mkdir()
            (root / "templates" / "base.html").write_text("<html></html>")
            found = violations(root)
            self.assertTrue(any("index.php" in v for v in found))
            self.assertTrue(any("base.html" in v for v in found))

    def test_structure_rejects_dotenv_and_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sources").mkdir()
            (root / "sources" / ".env").write_text("TOKEN=1")
            (root / "state.sqlite").write_bytes(b"")
            found = violations(root)
            self.assertTrue(any(".env" in v for v in found))
            self.assertTrue(any("sqlite" in v for v in found))

    def test_allowed_layout_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for item in ("scripts", "tests", "sources/seed/global",
                         "schemas", "state", "services", "collections",
                         "common", ".github/workflows"):
                (root / item).mkdir(parents=True, exist_ok=True)
            (root / "catalog.json").write_text("{}")
            (root / "README_RU.md").write_text("x")
            (root / "scripts" / "netlist_data").mkdir(parents=True)
            (root / "scripts" / "netlist_data" / "build.py").write_text("x")
            self.assertEqual(violations(root), [])


if __name__ == "__main__":
    unittest.main()
