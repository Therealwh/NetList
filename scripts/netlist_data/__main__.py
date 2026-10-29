"""CLI: python -m scripts.netlist_data <import|build|guards|check-structure>."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import build as build_mod
from . import check_structure, guards
from .seed_import import build_registry, load_seed_catalog, load_user_submissions, save_registry


def cmd_import(args: argparse.Namespace) -> int:
    source = Path(args.source)
    seed_root = Path(args.repo_root) / "sources" / "seed"
    for dataset in args.datasets:
        dst_dir = seed_root / dataset
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / dataset / "catalog.json", dst_dir / "catalog.json")
        copied = 1
        for csv_path in sorted((source / dataset).glob("*_services.csv")):
            shutil.copy2(csv_path, dst_dir / csv_path.name)
            copied += 1
        print(f"seed '{dataset}': catalog.json + {copied - 1} csv скопированы")
    records: list[dict] = []
    for dataset in args.datasets:
        records.extend(load_seed_catalog(seed_root, dataset))
    known_categories = {c for r in records for c in r["categories"]}
    user_records = load_user_submissions(Path(args.repo_root), known_categories=known_categories)
    if user_records:
        records.extend(user_records)
        print(f"пользовательских заявок импортировано: {len(user_records)}")
    registry = build_registry(records)
    save_registry(Path(args.repo_root), registry)
    domains = len({d for s in registry.values() for d in s.domains})
    print(f"сервисов: {len(registry)}; уникальных доменов: {domains}")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    catalog = build_mod.build_all(Path(args.repo_root))
    print(json.dumps(catalog["counts"], ensure_ascii=False))
    return 0


def cmd_guards(args: argparse.Namespace) -> int:
    catalog = json.loads(Path(args.catalog).read_text(encoding="utf-8"))
    problems = guards.check_against_previous(Path(args.repo_root), catalog)
    if problems:
        for problem in problems:
            print(f"GUARD: {problem}", file=sys.stderr)
        return 1
    guards.save_last_good(Path(args.repo_root), catalog)
    print("guards: ok")
    return 0


def cmd_check_structure(args: argparse.Namespace) -> int:
    return check_structure.main([args.repo_root])


def main(argv: list[str] | None = None) -> int:
    import sys

    if argv is None:
        argv = sys.argv[1:]
    parser = argparse.ArgumentParser(prog="netlist_data")
    parser.add_argument("--repo-root", default=".")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("import", help="скопировать seed и собрать реестр сервисов")
    p.add_argument("--source", required=True, help="папка netlist_seed_lists")
    p.add_argument("--datasets", nargs="+", default=["global", "russian"])
    p.set_defaults(func=cmd_import)

    sub.add_parser("build", help="пересобрать списки и catalog.json").set_defaults(func=cmd_build)

    p = sub.add_parser("guards", help="защита от потери данных")
    p.add_argument("--catalog", default="catalog.json")
    p.set_defaults(func=cmd_guards)

    sub.add_parser("check-structure", help="запрещённые файлы").set_defaults(
        func=cmd_check_structure
    )

    if argv and argv[0] == "logos":
        from . import logos

        return logos.main(argv)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
