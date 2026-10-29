import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.netlist_data.resolve_ips import generate


class ResolveIpsTest(unittest.TestCase):
    def test_generates_typed_files_and_exact_host_routes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "state" / "registry.json"
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({"services": [{
                "name": "Example",
                "slug": "example",
                "domains": ["example.com"],
                "categories": ["test"],
                "datasets": ["test"],
                "counts": {"example.com": 1},
            }]}), encoding="utf-8")

            with patch(
                "scripts.netlist_data.resolve_ips.resolve_domain",
                return_value=({"8.8.8.8"}, {"2001:4860:4860::8888"}),
            ):
                stats = generate(root)

            self.assertEqual(stats["ipv4"], 1)
            self.assertEqual(stats["ipv6"], 1)
            self.assertIn("8.8.8.8", (root / "services/example/ipv4.txt").read_text())
            self.assertIn("2001:4860:4860::8888", (root / "services/example/ipv6.txt").read_text())
            self.assertIn("8.8.8.8/32", (root / "services/example/cidrv4.txt").read_text())
            self.assertIn("2001:4860:4860::8888/128", (root / "services/example/cidrv6.txt").read_text())
            self.assertIn("8.8.8.8", (root / "common/ipv4.txt").read_text())

    def test_preserves_previous_snapshot_on_total_dns_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registry = root / "state" / "registry.json"
            registry.parent.mkdir(parents=True)
            registry.write_text(json.dumps({"services": [{
                "name": "Example",
                "slug": "example",
                "domains": ["example.com"],
                "categories": ["test"],
                "datasets": ["test"],
                "counts": {"example.com": 1},
            }]}), encoding="utf-8")
            service_dir = root / "services" / "example"
            service_dir.mkdir(parents=True)
            (service_dir / "ipv4.txt").write_text("8.8.8.8\n", encoding="utf-8")

            with patch(
                "scripts.netlist_data.resolve_ips.resolve_domain",
                return_value=(set(), set()),
            ):
                stats = generate(root)

            self.assertEqual(stats["services_using_last_known_snapshot"], 1)
            self.assertIn("8.8.8.8", (service_dir / "ipv4.txt").read_text())
            self.assertIn("8.8.8.8/32", (service_dir / "cidrv4.txt").read_text())


    def test_filters_rfc6598_shared_ipv4_space(self):
        import socket

        records = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("100.61.86.237", 0)),
        ]
        with patch("scripts.netlist_data.resolve_ips.socket.getaddrinfo", return_value=records):
            v4, v6 = __import__(
                "scripts.netlist_data.resolve_ips", fromlist=["resolve_domain"]
            ).resolve_domain("example.com")
        self.assertEqual(v4, {"8.8.8.8"})
        self.assertEqual(v6, set())


if __name__ == "__main__":
    unittest.main()
