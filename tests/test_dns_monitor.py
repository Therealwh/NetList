import json
import socket
import tempfile
import unittest
from pathlib import Path

from scripts.netlist_data.dns_monitor import monitor_catalog


class DnsMonitorTest(unittest.TestCase):
    def make_catalog(self, root):
        (root / "state").mkdir()
        (root / "catalog.json").write_text(json.dumps({
            "generated_at": "2026-11-01T00:00:00+00:00",
            "services": [
                {"name": "Example", "slug": "example", "domains": ["example.com", "www.example.com"]},
                {"name": "Alias", "slug": "alias", "domains": ["example.com"]},
            ],
        }), encoding="utf-8")

    def test_records_a_and_aaaa_independently_and_groups_owners(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_catalog(root)

            def checker(domain, family):
                if family == socket.AF_INET:
                    return {"status": "ok", "addresses": ["8.8.8.8"], "error": None}
                return {"status": "no_records", "addresses": [], "error": None}

            data = monitor_catalog(root, checker, "2026-11-01T00:00:00+00:00")
            item = data["domains"]["example.com"]
            self.assertEqual(item["ipv4"]["addresses"], ["8.8.8.8"])
            self.assertEqual(item["ipv4"]["status"], "ok")
            self.assertEqual(item["ipv6"]["status"], "no_records")
            self.assertEqual({x["slug"] for x in item["services"]}, {"example", "alias"})
            self.assertEqual(data["summary"]["domains_total"], 2)

    def test_transient_error_keeps_last_good_addresses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_catalog(root)
            first = monitor_catalog(
                root,
                lambda domain, family: {"status": "ok", "addresses": ["8.8.8.8"] if family == socket.AF_INET else ["2001:4860:4860::8888"], "error": None},
                "2026-11-01T00:00:00+00:00",
            )
            second = monitor_catalog(
                root,
                lambda domain, family: {"status": "error", "addresses": [], "error": "temporary timeout"},
                "2026-11-02T00:00:00+00:00",
            )
            item = second["domains"]["example.com"]
            self.assertEqual(item["ipv4"]["status"], "error")
            self.assertEqual(item["ipv4"]["addresses"], [])
            self.assertEqual(item["ipv4"]["last_good_addresses"], ["8.8.8.8"])
            self.assertEqual(item["ipv6"]["last_good_addresses"], ["2001:4860:4860::8888"])

    def test_history_tracks_address_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_catalog(root)
            monitor_catalog(root, lambda d, f: {"status": "ok", "addresses": ["8.8.8.8"], "error": None}, "2026-11-01T00:00:00+00:00")
            second = monitor_catalog(root, lambda d, f: {"status": "ok", "addresses": ["1.1.1.1"], "error": None}, "2026-11-02T00:00:00+00:00")
            self.assertEqual(second["domains"]["example.com"]["changed"], ["ipv4", "ipv6"])
            self.assertEqual(len(second["domains"]["example.com"]["history"]), 2)


if __name__ == "__main__":
    unittest.main()
