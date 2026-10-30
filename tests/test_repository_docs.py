"""Regression checks for the repository landing pages and published data links."""
from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+[^)]*)?\)")
RAW_URL = re.compile(r"https://raw\.githubusercontent\.com/Therealwh/NetList/main/([A-Za-z0-9_./-]+)")


class RepositoryDocsTest(unittest.TestCase):
    def test_bilingual_readmes_exist(self):
        for name in ("README.md", "README_EN.md", "README_RU.md"):
            with self.subTest(name=name):
                self.assertTrue((ROOT / name).is_file())

    def test_relative_markdown_links_resolve(self):
        for name in ("README.md", "README_EN.md", "README_RU.md"):
            content = (ROOT / name).read_text(encoding="utf-8")
            for target in MARKDOWN_LINK.findall(content):
                parsed = urlparse(target.strip("<>"))
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                path = (ROOT / unquote(parsed.path)).resolve()
                with self.subTest(readme=name, target=target):
                    self.assertTrue(path == ROOT or ROOT in path.parents,
                                    f"link escapes repository: {target}")
                    self.assertTrue(path.exists(), f"broken repository link: {target}")

    def test_raw_github_urls_point_to_real_files(self):
        for name in ("README.md", "README_EN.md"):
            content = (ROOT / name).read_text(encoding="utf-8")
            for raw_path in RAW_URL.findall(content):
                path = (ROOT / unquote(raw_path)).resolve()
                with self.subTest(readme=name, raw_path=raw_path):
                    self.assertTrue(path == ROOT or ROOT in path.parents,
                                    f"raw URL escapes repository: {raw_path}")
                    self.assertTrue(path.is_file() or path.is_dir(), f"broken Raw GitHub URL: {raw_path}")

    def test_key_data_formats_are_present(self):
        for relative in (
            "catalog.json",
            "common/domains.txt",
            "common/ipv4.txt",
            "common/ipv6.txt",
            "common/cidrv4.txt",
            "common/cidrv6.txt",
            "services/vk/domains.txt",
            "services/vk/ipv4.txt",
            "services/vk/ipv6.txt",
            "services/vk/cidrv4.txt",
            "services/vk/cidrv6.txt",
            "schemas/catalog.schema.json",
            "schemas/typed-lists.md",
        ):
            with self.subTest(path=relative):
                self.assertTrue((ROOT / relative).is_file())


if __name__ == "__main__":
    unittest.main()
