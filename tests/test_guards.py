import tempfile
import unittest
from pathlib import Path

from scripts.netlist_data.guards import check_against_previous, save_last_good


def catalog(total: int, services: list[dict] | None = None) -> dict:
    return {"counts": {"domains": total}, "services": services or []}


class GuardsTest(unittest.TestCase):
    def test_empty_build_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_last_good(root, catalog(100))
            problems = check_against_previous(root, catalog(0))
            self.assertTrue(any("0 domains" in p for p in problems))

    def test_guards_reject_mass_deletion(self):
        # Review Focus #3
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_last_good(root, catalog(100))
            problems = check_against_previous(root, catalog(50))
            self.assertTrue(any("dropped" in p for p in problems))

    def test_service_shrink_and_wipe_flagged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save_last_good(root, catalog(100, services=[
                {"slug": "vk", "domain_count": 10},
                {"slug": "ok", "domain_count": 6},
            ]))
            problems = check_against_previous(root, catalog(100, services=[
                {"slug": "vk", "domain_count": 4},   # усох >50%
                {"slug": "ok", "domain_count": 0},   # потерял всё
            ]))
            self.assertEqual(len(problems), 2)

    def test_pass_on_first_run_and_growth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(check_against_previous(root, catalog(100)), [])
            save_last_good(root, catalog(100))
            self.assertEqual(check_against_previous(root, catalog(120)), [])
            self.assertTrue((root / "state" / "last_good.json").exists())


if __name__ == "__main__":
    unittest.main()
