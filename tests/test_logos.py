import json
import tempfile
import unittest
from pathlib import Path

from scripts.netlist_data import logos


VALID_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M1 1h2v2H1z"/></svg>'
UNSAFE_SVG = b'<svg viewBox="0 0 24 24" onload="alert(1)"><script>alert(1)</script></svg>'


def make_repo(root: Path, manifest: dict | None = None, files: dict[str, bytes] | None = None) -> Path:
    logos_dir = logos.logos_dir(root)
    logos_dir.mkdir(parents=True, exist_ok=True)
    for name, body in (files or {}).items():
        (logos_dir / name).write_bytes(body)
    if manifest is not None:
        (logos_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return root


class ValidateSvgTest(unittest.TestCase):
    def test_valid_svg_passes(self):
        ok, reason = logos.validate_svg(VALID_SVG)
        self.assertTrue(ok, reason)

    def test_unsafe_constructs_rejected(self):
        for body in (UNSAFE_SVG, b"<svg viewBox='0 0 1 1'><foreignObject/></svg>",
                     b'<svg viewBox="0 0 1 1"><a href="javascript:x"/></svg>',
                     b'<svg viewBox="0 0 1 1"><a href="https://evil.example"/></svg>',
                     b"not svg at all", b""):
            ok, reason = logos.validate_svg(body)
            self.assertFalse(ok, body[:40])
            self.assertNotEqual(reason, "")


class CheckTest(unittest.TestCase):
    def entry(self, sid="vk", sha=None):
        return {"service_id": sid, "name": "VK", "primary_domain": "vk.com",
                "file": f"{sid}.svg", "source": "simple-icons", "license": "CC0",
                "checked_at": "2026-10-29T00:00:00+00:00", "sha256": sha or logos.sha256(VALID_SVG)}

    def test_check_detects_missing_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp), manifest={"version": 1, "logos": {"vk": self.entry()}})
            problems = logos.check(root)
            self.assertTrue(any("отсутствует" in p for p in problems))

    def test_check_detects_duplicate_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            dup = self.entry("vk2")
            dup["file"] = "vk.svg"  # два сервиса ссылаются на один файл
            root = make_repo(Path(tmp), manifest={"version": 1, "logos": {
                "vk": self.entry("vk"), "vk2": dup}}, files={"vk.svg": VALID_SVG})
            problems = logos.check(root)
            self.assertTrue(any("дублирование" in p for p in problems))

    def test_check_detects_bad_path_and_sha(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = self.entry()
            bad["file"] = "../evil.svg"
            wrong_sha = self.entry(sha="0" * 64)
            wrong_sha["file"] = "ok.svg"
            root = make_repo(Path(tmp), manifest={"version": 1, "logos": {"vk": bad, "ok": wrong_sha}},
                             files={"ok.svg": VALID_SVG})
            problems = logos.check(root)
            self.assertTrue(any("недопустимый путь" in p for p in problems))
            self.assertTrue(any("sha256" in p for p in problems))

    def test_check_passes_valid_set(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = make_repo(Path(tmp), manifest={"version": 1, "logos": {"vk": self.entry()}},
                             files={"vk.svg": VALID_SVG})
            self.assertEqual(logos.check(root), [])


class DiscoverTest(unittest.TestCase):
    def test_discover_downloads_valid_and_marks_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "catalog.json").write_text(json.dumps({"services": [
                {"slug": "vk", "name": "VK", "primary_domain": "vk.com"},
                {"slug": "superobscurе", "name": "Нет такого бренда", "primary_domain": "no.example"},
            ]}, ensure_ascii=False), encoding="utf-8")
            logos_dir = logos.logos_dir(root)
            logos_dir.mkdir(parents=True)
            (logos_dir / "sources.json").write_text(json.dumps({
                "vk": {"candidates": ["vk"], "source": "simple-icons", "license": "CC0"},
            }), encoding="utf-8")
            real_fetch = logos.fetch_cdn
            logos.fetch_cdn = lambda slug: VALID_SVG if slug == "vk" else None
            try:
                result = logos.build(root, discover=True)
            finally:
                logos.fetch_cdn = real_fetch
            self.assertIn("vk", result["added"])
            self.assertEqual(result["pending"], 1)
            manifest = json.loads((logos_dir / "manifest.json").read_text(encoding="utf-8"))
            self.assertIn("vk", manifest["logos"])
            self.assertEqual(len(manifest["pending"]), 1)
            self.assertEqual(logos.check(root), [])

    def test_official_fallbacks_are_saved_with_explicit_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "catalog.json").write_text(json.dumps({"services": [
                {"slug": "slack", "name": "Slack", "primary_domain": "slack.com"},
                {"slug": "canva", "name": "Canva", "primary_domain": "canva.com"},
            ]}), encoding="utf-8")
            folder = logos.logos_dir(root)
            folder.mkdir(parents=True)
            (folder / "sources.json").write_text(json.dumps({
                "slack": {"candidates": ["slack"], "source": "simple-icons", "license": "CC0"},
                "canva": {"candidates": ["canva"], "source": "simple-icons", "license": "CC0"},
            }), encoding="utf-8")
            original_cdn = logos.fetch_cdn
            original_fallback = logos.fetch_official_fallback
            logos.fetch_cdn = lambda _slug: None
            logos.fetch_official_fallback = lambda slug: (
                VALID_SVG, "official-test", "test brand guidance"
            ) if slug in {"slack", "canva"} else None
            try:
                result = logos.build(root, discover=True)
            finally:
                logos.fetch_cdn = original_cdn
                logos.fetch_official_fallback = original_fallback
            self.assertEqual(set(result["added"]), {"slack", "canva"})
            manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["logos"]["slack"]["source"], "official-test")
            self.assertEqual(manifest["logos"]["canva"]["license"], "test brand guidance")
            self.assertEqual(manifest["pending"], [])
            self.assertEqual(logos.check(root), [])


if __name__ == "__main__":
    unittest.main()
