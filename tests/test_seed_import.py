import json
import tempfile
import unittest
from pathlib import Path

from scripts.netlist_data.seed_import import (
    build_registry,
    load_registry,
    load_seed_catalog,
    primary_domain,
    save_registry,
)


def write_seed(root: Path, dataset: str, categories: list[dict]) -> None:
    directory = root / dataset
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "catalog.json").write_text(json.dumps({
        "schema_version": 1, "dataset": dataset, "notice": "test",
        "categories": categories,
    }, ensure_ascii=False), encoding="utf-8")


class SeedImportTest(unittest.TestCase):
    def test_regenerates_broken_slugs(self):
        # Review Focus #1: seed-слаги 'service'/'1'/'2' игнорируются, слаг из имени
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_seed(root, "russian", [{
                "id": "search_ecosystems",
                "services": [
                    {"name": "Яндекс", "slug": "service", "domains": ["yandex.ru", "ya.ru"]},
                    {"name": "2ГИС", "slug": "2", "domains": ["2gis.ru"]},
                    {"name": "1С", "slug": "1", "domains": ["1c.ru"]},
                    {"name": "Т2", "slug": "2", "domains": ["t2.ru", "tele2.ru"]},
                ],
            }])
            registry = build_registry(load_seed_catalog(root, "russian"))
            self.assertEqual(sorted(registry), ["1c", "2gis", "t2", "yandex"])

    def test_invalid_domains_dropped_and_templates_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_seed(root, "global", [{
                "id": "movies",
                "services": [{"name": "Test", "slug": "test",
                              "domains": ["ok.ru", "*.wild.ru", "localhost", "one"]}],
            }])
            records = load_seed_catalog(root, "global")
            self.assertEqual(records[0]["domains"], {"ok.ru"})

    def test_merge_same_service_across_datasets(self):
        # Review Focus #2: VK в global(social) и russian(search_ecosystems) — один сервис
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_seed(root, "global", [{"id": "social", "services": [
                {"name": "VK", "slug": "vk", "domains": ["vk.com", "vk.ru"]},
                {"name": "Ozon", "slug": "ozon", "domains": ["ozon.ru"]},
            ]}])
            write_seed(root, "russian", [{"id": "search_ecosystems", "services": [
                {"name": "VK", "slug": "vk", "domains": ["vk.com", "userapi.com"]},
            ]}])
            records = load_seed_catalog(root, "global") + load_seed_catalog(root, "russian")
            registry = build_registry(records)
            self.assertEqual(len(registry), 2)
            vk = registry["vk"]
            self.assertEqual(vk.domains, {"vk.com", "vk.ru", "userapi.com"})
            self.assertEqual(vk.categories, {"social", "search_ecosystems"})
            self.assertEqual(vk.datasets, {"global", "russian"})

    def test_primary_domain_prefers_frequent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_seed(root, "russian", [{"id": "search_ecosystems", "services": [
                {"name": "VK", "slug": "vk", "domains": ["vk.com", "vk.ru", "userapi.com"]},
                {"name": "VK", "slug": "vk", "domains": ["vk.com", "vk.ru"]},
            ]}])
            registry = build_registry(load_seed_catalog(root, "russian"))
            self.assertEqual(primary_domain(registry["vk"]), "vk.com")

    def test_registry_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_seed(root, "global", [{"id": "social", "services": [
                {"name": "VK", "slug": "vk", "domains": ["vk.com"]},
            ]}])
            registry = build_registry(load_seed_catalog(root, "global"))
            save_registry(root, registry)
            loaded = load_registry(root / "state" / "registry.json")
            self.assertEqual(loaded["vk"].domains, {"vk.com"})
            self.assertEqual(loaded["vk"].categories, {"social"})


if __name__ == "__main__":
    unittest.main()
