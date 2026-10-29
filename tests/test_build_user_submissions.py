import json
import tempfile
import unittest
from pathlib import Path

from scripts.netlist_data.build import build_all
from scripts.netlist_data.seed_import import Service, save_registry


class BuildUserSubmissionsTest(unittest.TestCase):
    def test_published_submission_is_included_on_every_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_registry(root, {
                "existing": Service(
                    name="Existing Service",
                    slug="existing",
                    domains={"existing.example"},
                    categories={"social"},
                    datasets={"global"},
                    counts={"existing.example": 1},
                )
            })
            submissions = root / "sources" / "user_submissions"
            submissions.mkdir(parents=True)
            (submissions / "123.json").write_text(json.dumps({
                "submission_id": 123,
                "name": "Example Org",
                "domain": "example.org",
                "categories": ["social"],
            }), encoding="utf-8")

            first = build_all(root)
            second = build_all(root)

            slugs = {service["slug"] for service in first["services"]}
            self.assertIn("example-org", slugs)
            user_service = next(s for s in first["services"] if s["slug"] == "example-org")
            self.assertEqual(user_service["domains"], ["example.org"])
            self.assertIn("example-org", {s["slug"] for s in second["services"]})
            self.assertEqual(first["counts"], second["counts"])


if __name__ == "__main__":
    unittest.main()
