# NetList — репозиторий данных

Публичный источник истины NetList: сетевые списки, скрипты обработки и генерации,
конфигурация источников и автоматизация обновлений.

> Код сайта живёт в приватном репозитории [Therealwh/NetList_Site](https://github.com/Therealwh/NetList_Site)
> и получает опубликованные данные этого репозитория по raw-HTTPS с локальным кешем.
> Правила распределения файлов и публикации — в `DEPLOYMENT.md` репозитория сайта.


Списки доменов (далее IPv4/IPv6/CIDR) по сервисам и категориям. **Наличие домена
в списке не подтверждает блокировку, доступность или принадлежность IP сервису** —
это стартовые кандидаты, требующие проверки.

## Структура
- `services/<slug>/domains.txt` — списки по сервисам (потом: ipv4.txt, ipv6.txt, cidrv4.txt, cidrv6.txt).
- `collections/<category>/domains.txt` — агрегаты по категориям.
- `common/domains.txt` — объединённый список.
- `catalog.json` — публичный каталог: сервисы, категории, счётчики, `generated_at`.
- `sources/seed/` — начальные датасеты (global, russian), источник истины импорта.
- `schemas/` — JSON-схема каталога.
- `state/last_good.json`, `state/registry.json` — защита от потерь и реестр сервисов (коммитятся).
- `scripts/netlist_data/` — сборка (только stdlib Python 3.12).

## Команды

    python -m scripts.netlist_data import --source ../netlist_seed_lists
    python -m scripts.netlist_data build
    python -m scripts.netlist_data guards
    python -m scripts.netlist_data check-structure
    python -m unittest discover -s tests -v

## Обновление
GitHub Actions `.github/workflows/update-lists.yml`: ежедневно 03:00 UTC и вручную
(workflow_dispatch). Порядок: check-structure → тесты → build → guards → commit
только при реальных изменениях контента. Пустой или резко усохший источник
останавливает публикацию; последняя корректная версия остаётся в git.

## Что запрещено в репозитории
Код сайта (PHP/HTML/CSS/JS), шаблоны, админ-панель, БД, `.env`, секреты,
`vendor/`, `node_modules/`, логи, бэкапы. Проверяется `check-structure`
и шагом CI. Сайт NetList живёт в отдельном репозитории и получает данные
через raw-файлы GitHub.
