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


    def test_first_snapshot_is_baseline_not_a_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_catalog(root)
            data = monitor_catalog(
                root,
                lambda domain, family: {"status": "ok", "addresses": ["8.8.8.8"], "error": None},
                "2026-11-01T00:00:00+00:00",
            )
            self.assertEqual(data["summary"]["domains_changed"], 0)
            self.assertEqual(data["domains"]["example.com"]["changed"], [])


    def test_recovery_to_same_last_good_addresses_is_not_a_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_catalog(root)
            good = lambda domain, family: {"status": "ok", "addresses": ["8.8.8.8"] if family == socket.AF_INET else ["2001:4860:4860::8888"], "error": None}
            failed = lambda domain, family: {"status": "error", "addresses": [], "error": "temporary timeout"}
            monitor_catalog(root, good, "2026-11-01T00:00:00+00:00")
            monitor_catalog(root, failed, "2026-11-02T00:00:00+00:00")
            recovered = monitor_catalog(root, good, "2026-11-03T00:00:00+00:00")
            self.assertEqual(recovered["domains"]["example.com"]["changed"], [])
            self.assertEqual(recovered["summary"]["domains_changed"], 0)


    def test_global_history_tracks_domain_and_ip_additions_removals(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_catalog(root)
            good = lambda d, f: {"status": "ok", "addresses": ["8.8.8.8"] if f == socket.AF_INET else ["2001:4860:4860::8888"], "error": None}
            first = monitor_catalog(root, good, "2026-11-01T00:00:00+00:00")
            events1 = json.loads((root / "state" / "dns_history.json").read_text())["events"]
            self.assertEqual(sum(e["type"] == "domain_added" for e in events1), 2)
            self.assertEqual(sum(e["type"] == "ip_added" for e in events1), 0)  # baseline is not a change

            second = monitor_catalog(root, lambda d, f: {"status": "ok", "addresses": ["1.1.1.1"] if f == socket.AF_INET else ["2606:4700:4700::1111"], "error": None}, "2026-11-02T00:00:00+00:00")
            events2 = json.loads((root / "state" / "dns_history.json").read_text())["events"]
            self.assertEqual(sum(e["type"] == "ip_added" for e in events2), 4)
            self.assertEqual(sum(e["type"] == "ip_removed" for e in events2), 4)

            catalog = json.loads((root / "catalog.json").read_text())
            catalog["services"] = [{"name": "Example", "slug": "example", "domains": ["example.com"]}]
            (root / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
            third = monitor_catalog(root, good, "2026-11-03T00:00:00+00:00")
            events3 = json.loads((root / "state" / "dns_history.json").read_text())["events"]
            self.assertTrue(any(e["type"] == "domain_removed" and e["domain"] == "www.example.com" for e in events3))

    def test_dns_errors_do_not_create_ip_removal_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_catalog(root)
            good = lambda d, f: {"status": "ok", "addresses": ["8.8.8.8"], "error": None}
            failed = lambda d, f: {"status": "error", "addresses": [], "error": "timeout"}
            monitor_catalog(root, good, "2026-11-01T00:00:00+00:00")
            monitor_catalog(root, failed, "2026-11-02T00:00:00+00:00")
            events = json.loads((root / "state" / "dns_history.json").read_text())["events"]
            self.assertFalse(any(e["type"] == "ip_removed" for e in events))

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
