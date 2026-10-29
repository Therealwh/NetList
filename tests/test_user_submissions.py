import json
import tempfile
import unittest
from pathlib import Path

from scripts.netlist_data.seed_import import build_registry, load_user_submissions


def write_submission(root: Path, payload: dict, name: str = "1.json") -> None:
    directory = root / "sources" / "user_submissions"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


class UserSubmissionsTest(unittest.TestCase):
    def test_user_submission_imported_with_known_category_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_submission(root, {
                "submission_id": 1, "domain": "example.org", "name": "example.org",
                "categories": ["movies", "fake_cat"], "subdomains": [], "ipv4": [], "ipv6": [],
            })
            records = load_user_submissions(root, known_categories={"movies", "social"})
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["categories"], {"movies"})
            self.assertEqual(records[0]["dataset"], "user")
            registry = build_registry(records)
            self.assertIn("example-org", registry)
            self.assertEqual(registry["example-org"].domains, {"example.org"})

    def test_without_known_category_falls_back_to_user_collections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_submission(root, {"domain": "a.example", "categories": ["unknown-cat"]}, name="2.json")
            records = load_user_submissions(root, known_categories={"movies"})
            self.assertEqual(records[0]["categories"], {"user_collections"})

    def test_invalid_or_broken_submissions_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_submission(root, {"domain": "*.template", "categories": ["movies"]}, name="3.json")
            write_submission(root, {"categories": ["movies"]}, name="4.json")
            (root / "sources" / "user_submissions" / "5.json").write_text("{broken", encoding="utf-8")
            self.assertEqual(load_user_submissions(root, known_categories={"movies"}), [])

    def test_missing_directory_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_user_submissions(Path(tmp), known_categories={"movies"}), [])


if __name__ == "__main__":
    unittest.main()
