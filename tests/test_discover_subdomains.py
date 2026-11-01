import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.netlist_data.discover_subdomains import discover, query_certificate_transparency
from scripts.netlist_data.seed_import import Service, save_registry
from scripts.netlist_data.build import build_all


class DiscoverSubdomainsTest(unittest.TestCase):
    def test_ct_results_are_normalized_and_limited_to_submitted_domain(self):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self, size=-1):
                return json.dumps([
                    {"name_value": "*.api.example.org\ncdn.example.org"},
                    {"name_value": "example.org.evil.test\noutside.test"},
                ]).encode()

        with patch("scripts.netlist_data.discover_subdomains.urlopen", return_value=Response()):
            self.assertEqual(
                query_certificate_transparency("example.org"),
                {"api.example.org", "cdn.example.org"},
            )

    def test_discovery_is_persisted_and_added_to_service_domains(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            submissions = root / "sources" / "user_submissions"
            submissions.mkdir(parents=True)
            (submissions / "1.json").write_text(json.dumps({
                "name": "Example",
                "domain": "example.org",
                "categories": ["social"],
            }), encoding="utf-8")
            save_registry(root, {
                "example": Service(
                    name="Example", slug="example", domains={"example.org"},
                    categories={"social"}, datasets={"global"}, counts={"example.org": 1},
                )
            })
            with patch(
                "scripts.netlist_data.discover_subdomains.query_certificate_transparency",
                return_value={"example.org", "api.example.org", "cdn.example.org"},
            ):
                stats = discover(root)
            self.assertEqual(stats["roots_checked"], 1)
            catalog = build_all(root)
            service = next(item for item in catalog["services"] if item["slug"] == "example")
            self.assertIn("api.example.org", service["domains"])
            self.assertIn("cdn.example.org", service["domains"])
            self.assertIn("example.org", service["domains"])
            saved = json.loads((root / "state/discovered_subdomains.json").read_text())
            self.assertTrue(all(item["source"] == "crt.sh" for item in saved["domains"]))


if __name__ == "__main__":
    unittest.main()
