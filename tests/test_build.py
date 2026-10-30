import json
import tempfile
import unittest
from pathlib import Path

from scripts.netlist_data.build import build_all
from scripts.netlist_data.seed_import import build_registry, load_seed_catalog, save_registry
from tests.test_seed_import import write_seed


class BuildTest(unittest.TestCase):
    def build(self, root: Path) -> dict:
        write_seed(root, "global", [{"id": "social", "services": [
            {"name": "VK", "slug": "vk", "domains": ["vk.com", "vk.ru"]},
            {"name": "Reddit", "slug": "reddit", "domains": ["reddit.com"]},
        ]}, {"id": "gaming", "services": [
            {"name": "Steam", "slug": "steam", "domains": ["steampowered.com", "steamcommunity.com"]},
        ]}])
        records = load_seed_catalog(root, "global")
        save_registry(root, build_registry(records))
        return build_all(root)

    def test_build_writes_all_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = self.build(root)
            self.assertTrue((root / "services" / "vk" / "domains.txt").exists())
            self.assertTrue((root / "collections" / "social" / "domains.txt").exists())
            self.assertTrue((root / "common" / "domains.txt").exists())
            self.assertEqual(catalog["counts"], {"services": 3, "categories": 2, "domains": 5})
            steam = next(s for s in catalog["services"] if s["slug"] == "steam")
            self.assertEqual(steam["primary_domain"], "steamcommunity.com")
            self.assertEqual(steam["seed_status"], "candidate_unverified")
            common = (root / "common" / "domains.txt").read_text(encoding="utf-8")
            for domain in ("vk.com", "reddit.com", "steampowered.com"):
                self.assertIn(domain, common)

    def test_common_domains_preserve_service_groups(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build(root)
            common = (root / "common" / "domains.txt").read_text(encoding="utf-8")
            self.assertIn("# Service — VK", common)
            self.assertIn("# Service — Reddit", common)
            self.assertIn("# Service — Steam", common)
            self.assertLess(common.index("# Service — Reddit"), common.index("reddit.com"))
            self.assertLess(common.index("# Service — Steam"), common.index("steamcommunity.com"))
            self.assertIn("# Service — VK\nvk.com\nvk.ru", common)

    def test_rebuild_keeps_generated_at_when_content_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.build(root)
            second = build_all(root)
            self.assertEqual(first["generated_at"], second["generated_at"])

    def test_catalog_has_no_unverified_claims(self):
        # Review Focus #5: каталог не утверждает статусы доступа без источника
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            catalog = self.build(root)
            self.assertIn("notice", catalog)
            for service in catalog["services"]:
                self.assertEqual(service["seed_status"], "candidate_unverified")
                for forbidden in ("status", "blocked", "restricted"):
                    self.assertNotIn(forbidden, service)


if __name__ == "__main__":
    unittest.main()
