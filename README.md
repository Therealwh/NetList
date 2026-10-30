# NetList

**Сетевые списки доменов, IPv4, IPv6 и CIDR для сетевых инструментов и роутеров.**

[![CI](https://github.com/Therealwh/NetList/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Therealwh/NetList/actions/workflows/ci.yml)
[![Обновление списков](https://github.com/Therealwh/NetList/actions/workflows/update-lists.yml/badge.svg?branch=main)](https://github.com/Therealwh/NetList/actions/workflows/update-lists.yml)
![Форматы](https://img.shields.io/badge/data-Domains%20%7C%20IPv4%20%7C%20IPv6%20%7C%20CIDR-536dfe)
[![Сайт](https://img.shields.io/badge/website-netlist.pro-2563eb?logo=googlechrome&logoColor=white)](https://netlist.pro)

[English](README_EN.md) · **Русский**

> [!TIP]
> **Помогите поддерживать списки актуальными.** Нашли нужный домен или заметили, что запись устарела? Добавьте предложение через [форму NetList](https://netlist.pro/submit-domain). Каждое предложение проходит проверку перед публикацией. Добавляя свои домены через сайт, вы помогаете поддерживать наборы данных полезными и актуальными для всего сообщества.

## Навигация

- [Сайт NetList](https://netlist.pro) · [Каталог списков](https://netlist.pro/lists) · [Категории](https://netlist.pro/categories)
- [Каталог данных](catalog.json) · [Общие списки](common/) · [Списки по сервисам](services/) · [Списки по категориям](collections/)
- [Типизированные IP/CIDR-списки](schemas/typed-lists.md) · [JSON-схема каталога](schemas/catalog.schema.json) · [Сведения об источниках](sources/seed/global/domain-sources.json)
- [GitHub Actions](https://github.com/Therealwh/NetList/actions) · [Сообщить об ошибке](https://github.com/Therealwh/NetList/issues/new) · [Pull Requests](https://github.com/Therealwh/NetList/pulls)

## Что такое NetList

NetList — публичный репозиторий-источник структурированных сетевых данных для сайта [netlist.pro](https://netlist.pro). Его задача — собирать, нормализовать, проверять, регулярно обновлять и публиковать домены и DNS-снимки IP-адресов, сгруппированные по сервисам и тематическим категориям. Сайт использует эти данные как основу для удобного конструктора: пользователь выбирает нужные сервисы или категории, собирает собственный набор доменов и IP/CIDR и скачивает его для настройки роутера, VPN-клиента или правил раздельной маршрутизации. В репозитории хранятся именно исходные данные для такого выбора, а не готовая конфигурация одного конкретного VPN-сервиса.

**NetList не является готовым универсальным блок-листом.** Это каталог кандидатов для технической настройки. Перед применением проверьте, какие именно хосты и адреса нужны вашему сценарию.

## Как NetList используется для настройки VPN и раздельной маршрутизации

Один и тот же набор доменов и IP можно применять **по-разному** — это зависит не от самого файла NetList, а от того, как в роутере или VPN-программе настроены правила. Сайт нужен, чтобы было удобно выбрать нужные сервисы и собрать из данных репозитория список именно под вашу схему.

### 1. Отправлять выбранные ресурсы через VPN или WireGuard

В этом режиме список работает как правило **«эти адреса направлять в VPN»**. В него добавляют домены и IP ресурсов, к которым нужно подключаться через VPN-туннель: например, заблокированные или недоступные напрямую сайты и сервисы.

**Пример:** в вашей схеме на роутере с WG 3.1 нужно указать заблокированные домены и IP, чтобы обращения к ним шли через WireGuard, а остальной трафик продолжал идти обычным маршрутом. Для этого на сайте можно выбрать нужные сервисы, сформировать список и использовать его в соответствующем разделе правил роутера — если установленная прошивка поддерживает такой формат импорта.

### 2. Открывать выбранные ресурсы напрямую, в обход VPN

В другом режиме список работает наоборот: **«эти адреса не отправлять в VPN»**. Такие правила также называют *bypass*, *direct*, *исключить из VPN* или *маршрутизировать напрямую*. В список могут добавлять российские, локальные или другие ресурсы, которые должны открываться через обычного интернет-провайдера, а не через VPN-туннель.

**Пример:** у пользователя весь интернет по умолчанию проходит через VPN, но он хочет, чтобы российские сайты, банки или локальные сервисы открывались напрямую. Он выбирает нужные ресурсы на сайте NetList и применяет полученный список как список исключений из VPN.

### Главное — направление правила выбираете вы

| Ваша задача | Что означает список в настройках |
|---|---|
| Заблокированные или недоступные напрямую ресурсы должны идти через VPN | Направлять выбранные домены и IP **в VPN** |
| Российские или локальные ресурсы должны идти через провайдера | Направлять выбранные домены и IP **напрямую, мимо VPN** |
| Нужны оба сценария | Сформировать и использовать **два отдельных списка** с разными действиями |

NetList намеренно не присваивает каждому домену универсальную метку «обязательно через VPN» или «обязательно напрямую». Один пользователь может направлять определённый сайт в туннель, а другой — исключать его из туннеля. Это зависит от страны, провайдера, текущей доступности ресурса, конфигурации роутера и личных предпочтений.

Категория в NetList обозначает, **к какому сервису или тематике относится ресурс**, а не то, куда его нужно маршрутизировать. Например, наличие домена в категории «Социальные сети» не означает автоматически, что его нужно отправлять через VPN или обходить VPN.

На сайте [netlist.pro](https://netlist.pro) можно использовать общий каталог, выбирать отдельные сервисы и категории и собирать набор под свою задачу. Если вашему устройству нужны не только домены, но и IP-адреса или CIDR, в репозитории для этого предусмотрены отдельные файлы. Поддерживаемый формат, способ импорта и названия режимов зависят от конкретной прошивки и программы.

### NetList и роутеры

Списки NetList можно использовать как источник доменных и IP/CIDR-данных для правил «через VPN» и «напрямую, в обход VPN». Какое именно действие назначить выбранным адресам, определяет пользователь в настройках своего роутера или VPN-клиента. Для обсуждения настройки роутера также указан ресурс [4PDA — тема 1123087](https://4pda.to/forum/index.php?showtopic=1123087). Совместимость конкретной прошивки, синтаксис правил и безопасный объём импорта проверяйте отдельно.

## Какие данные доступны

| Тип | Где находится | Что содержит |
|---|---|---|
| Домены | `domains.txt` | Нормализованные доменные имена |
| IPv4 | `ipv4.txt` | Публичные IPv4-адреса, полученные из DNS |
| IPv6 | `ipv6.txt` | Публичные IPv6-адреса, полученные из DNS |
| CIDRv4 | `cidrv4.txt` | Точные IPv4 host routes с префиксом `/32` |
| CIDRv6 | `cidrv6.txt` | Точные IPv6 host routes с префиксом `/128` |

Общие файлы находятся в [common/](common/), файлы отдельных сервисов — в [services/](services/). У каждого сервиса используется собственный каталог, например [VK](services/vk/), [Telegram](services/telegram/) или [YouTube](services/youtube/). Категориальные подборки публикуются в [collections/](collections/) и сейчас содержат агрегированные доменные списки.

### Общие списки

| Набор | Файл в репозитории | Raw URL |
|---|---|---|
| Все домены | [common/domains.txt](common/domains.txt) | [Скачать](https://raw.githubusercontent.com/Therealwh/NetList/main/common/domains.txt) |
| IPv4 | [common/ipv4.txt](common/ipv4.txt) | [Скачать](https://raw.githubusercontent.com/Therealwh/NetList/main/common/ipv4.txt) |
| IPv6 | [common/ipv6.txt](common/ipv6.txt) | [Скачать](https://raw.githubusercontent.com/Therealwh/NetList/main/common/ipv6.txt) |
| CIDRv4 | [common/cidrv4.txt](common/cidrv4.txt) | [Скачать](https://raw.githubusercontent.com/Therealwh/NetList/main/common/cidrv4.txt) |
| CIDRv6 | [common/cidrv6.txt](common/cidrv6.txt) | [Скачать](https://raw.githubusercontent.com/Therealwh/NetList/main/common/cidrv6.txt) |
| Каталог JSON | [catalog.json](catalog.json) | [Raw JSON](https://raw.githubusercontent.com/Therealwh/NetList/main/catalog.json) |

### Примеры списков отдельного сервиса

Все пять типов файлов проверены на примере [VK](services/vk/):

- [Домены VK](services/vk/domains.txt)
- [IPv4 VK](services/vk/ipv4.txt)
- [IPv6 VK](services/vk/ipv6.txt)
- [CIDRv4 VK](services/vk/cidrv4.txt)
- [CIDRv6 VK](services/vk/cidrv6.txt)

Raw URL строится по шаблону:

`https://raw.githubusercontent.com/Therealwh/NetList/main/services/<slug>/<file>.txt`

Например: `services/telegram/domains.txt` или `services/youtube/domains.txt`.

### Категории

Каждая ссылка ведёт на реальный файл `collections/<category>/domains.txt`.

| Категория | Файл |
|---|---|
| 18+ | [adult_18](collections/adult_18/domains.txt) |
| Искусственный интеллект | [ai](collections/ai/domains.txt) |
| Банки и платежи | [banks_payments](collections/banks_payments/domains.txt) |
| Облака и CDN | [cloud_cdn](collections/cloud_cdn/domains.txt) |
| Инструменты разработчика | [developer_tools](collections/developer_tools/domains.txt) |
| Обмен файлами | [file_sharing](collections/file_sharing/domains.txt) |
| Финансы и маркетплейсы | [finance_marketplaces](collections/finance_marketplaces/domains.txt) |
| Азартные игры | [gambling](collections/gambling/domains.txt) |
| Игры | [gaming](collections/gaming/domains.txt) |
| Государственные сервисы | [government](collections/government/domains.txt) |
| Здоровье и спорт | [health_sport](collections/health_sport/domains.txt) |
| IT, бизнес и образование | [it_business_education](collections/it_business_education/domains.txt) |
| Почта | [mail](collections/mail/domains.txt) |
| Маркетплейсы и доставка | [marketplaces_delivery](collections/marketplaces_delivery/domains.txt) |
| Мессенджеры | [messengers](collections/messengers/domains.txt) |
| Связь и телеком | [messengers_telecom](collections/messengers_telecom/domains.txt) |
| Кино | [movies](collections/movies/domains.txt) |
| Музыка | [music](collections/music/domains.txt) |
| Новости и образование | [news_education](collections/news_education/domains.txt) |
| ОС и безопасность | [os_security](collections/os_security/domains.txt) |
| Поисковые экосистемы | [search_ecosystems](collections/search_ecosystems/domains.txt) |
| Поисковые порталы | [search_portals](collections/search_portals/domains.txt) |
| Социальные сети | [social](collections/social/domains.txt) |
| Торренты и P2P | [torrents_p2p](collections/torrents_p2p/domains.txt) |
| Транспорт | [transport](collections/transport/domains.txt) |
| Видео, музыка и медиа | [video_music_media](collections/video_music_media/domains.txt) |
| Видеостриминг | [video_streaming](collections/video_streaming/domains.txt) |

## Быстрый старт

### Скачать через curl

Linux, macOS, роутер с поддержкой `curl`:

```bash
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/common/domains.txt" -o domains.txt
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/common/ipv4.txt" -o ipv4.txt
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/common/ipv6.txt" -o ipv6.txt
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/common/cidrv4.txt" -o cidrv4.txt
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/common/cidrv6.txt" -o cidrv6.txt
```

Загрузить домены конкретного сервиса:

```bash
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/services/vk/domains.txt" -o vk-domains.txt
```

### Скачать через PowerShell

```powershell
$base = "https://raw.githubusercontent.com/Therealwh/NetList/main/common"
Invoke-WebRequest "$base/domains.txt" -OutFile ".\domains.txt"
Invoke-WebRequest "$base/ipv4.txt" -OutFile ".\ipv4.txt"
Invoke-WebRequest "$base/ipv6.txt" -OutFile ".\ipv6.txt"
Invoke-WebRequest "$base/cidrv4.txt" -OutFile ".\cidrv4.txt"
Invoke-WebRequest "$base/cidrv6.txt" -OutFile ".\cidrv6.txt"
```

### Raw GitHub URL

Файлы можно читать напрямую без клонирования репозитория:

```text
https://raw.githubusercontent.com/Therealwh/NetList/main/<path>
```

Вместо `<path>` укажите реальный путь, например `common/domains.txt`, `collections/social/domains.txt` или `services/telegram/ipv4.txt`. Raw URL указывает на ветку `main`, поэтому после публикации обновлений по тому же адресу будет доступно новое содержимое. При необходимости закрепите commit SHA для воспроизводимых сборок.

## Каталог и документация

- [catalog.json](catalog.json) — версия схемы, время генерации, счётчики, категории и сервисы.
- [JSON Schema](schemas/catalog.schema.json) — структура каталога.
- [Typed lists](schemas/typed-lists.md) — описание генерации IP- и CIDR-файлов.
- [Domain source provenance](sources/seed/global/domain-sources.json) — часть источников и пояснений к добавленным доменам.
- [Seed: global](sources/seed/global/) · [Seed: Russian](sources/seed/russian/) · [User submissions](sources/user_submissions/).

Актуальные значения числа сервисов, категорий и доменов берите из `catalog.json`: счётчики там генерируются сборщиком, поэтому README не хранит устаревающие вручную числа.

## Как формируются данные

1. **Seed и реестр.** Начальные наборы находятся в `sources/seed/global/` и `sources/seed/russian/`; реестр сервисов хранится в `state/registry.json`. Избранные источники и обоснования перечислены в `sources/seed/global/domain-sources.json`.
2. **Предложения пользователей.** Проверенные модератором предложения сайта попадают в `sources/user_submissions/` и участвуют в последующей сборке. Наличие заявки ещё не означает подтверждение принадлежности домена сервису.
3. **Нормализация.** Домен приводится к нижнему регистру и ASCII/IDNA (punycode); некорректные имена, wildcard, localhost и неподходящие значения отбрасываются. IP и CIDR приводятся к каноническому виду средствами Python `ipaddress`.
4. **Дедупликация.** Внутри сервисов и агрегатов записи нормализуются, сортируются и дедуплицируются. Один домен может относиться к нескольким сервисам, поэтому он может повторяться в сгруппированном `common/domains.txt`.
5. **DNS-снимки.** Обновление разрешает домены через системный DNS resolver и формирует списки публичных IPv4/IPv6. CIDRv4/CIDRv6 — это точные host routes `/32` и `/128` для полученных адресов, а не заявка на владение диапазоном.
6. **Защита от потери данных.** Если для сервиса DNS временно не дал адресов, сохраняется его предыдущий снимок. Guard-проверка останавливает публикацию при нулевом наборе или резком сокращении общего числа доменов/данных сервиса.
7. **Публикация.** Workflow добавляет в commit только разрешённые сгенерированные каталоги и файлы; пустой commit не создаётся.

Важно: ежедневный workflow пересобирает сохранённый реестр и пользовательские предложения, а также обновляет DNS-снимки. Он не является универсальным сканером интернета и не скачивает автоматически все внешние источники seed-каталогов.

## Автоматическое обновление и проверки

| Workflow | Назначение |
|---|---|
| [update-lists.yml](.github/workflows/update-lists.yml) | Сборка, DNS-снимки, guard-проверки и публикация изменений |
| [ci.yml](.github/workflows/ci.yml) | Проверка структуры, unit-тесты, сборка каталога и защита данных |

- **Расписание:** ежедневно в 03:00 UTC.
- **Ручной запуск:** GitHub → Actions → **update-lists** → **Run workflow** → ветка `main`.
- **CI:** запускается при Pull Request, push в `main` и вручную.
- **Среда сборки:** Python 3.12, стандартная библиотека Python.
- **Защита от резкого сокращения:** guard проверяет общий объём и изменения по сервисам; при подозрительном падении workflow завершается ошибкой и не публикует новую версию.
- **Область commit:** workflow не использует безусловный `git add -A`; публикуются только явно разрешённые пути данных и генерации.

Статус выполнения смотри в [GitHub Actions](https://github.com/Therealwh/NetList/actions).

## Как помочь проекту

1. Откройте [форму предложения домена](https://netlist.pro/submit-domain).
2. Укажите домен, при необходимости название сервиса, категорию и ссылку на источник.
3. Дождитесь проверки модератором. Не отправляйте пароли, токены, приватные адреса или конфиденциальные сведения.
4. Для исправления опубликованной записи создайте [Issue](https://github.com/Therealwh/NetList/issues/new) с путём к файлу и подтверждающими материалами либо подготовьте Pull Request.

Предложения не попадают в опубликованный каталог автоматически: их назначение — дать сопровождающему материал для проверки.

## Достоверность и ограничения

- Наличие домена в NetList **не доказывает блокировку**, недоступность или обязательность домена для работы сервиса.
- DNS-ответы меняются со временем; опубликованный IP — снимок на момент последнего успешного разрешения.
- Один IP может обслуживать разные сайты через CDN, reverse proxy или общий хостинг. Он не обязательно принадлежит указанному сервису.
- CIDR в текущей генерации означает точный host route (`/32` или `/128`), а не диапазон инфраструктуры компании.
- Списки могут быть неполными, содержать устаревшие или спорные записи и требуют проверки под конкретную прошивку, приложение и сетевую задачу.
- Используйте данные как техническую отправную точку, а не как гарантию доступности или точности.

## FAQ

**Это готовый блок-лист?**  
Нет. Это набор кандидатов для настройки сетевых правил. Сначала проверьте назначение каждой записи.

**Почему один IP встречается несколько раз?**  
Один адрес может возвращаться для нескольких доменов или использоваться общей CDN/хостинг-платформой. В сгруппированных файлах повторы между группами намеренные.

**Почему CIDR выглядит как `/32` или `/128`?**  
Это отдельный IPv4- или IPv6-адрес, записанный как точный маршрут. Такой формат не означает, что NetList определил всю подсеть сервиса.

**Можно ли использовать данные на роутере?**  
Да, если прошивка поддерживает импорт или преобразование TXT-доменов, IP и host-route списков. Формат и правила применения зависят от конкретного ПО роутера.

**Как часто обновляются данные?**  
Workflow запускается ежедневно в 03:00 UTC, а также при push в `main` и вручную. DNS-снимки зависят от доступности и ответов DNS в момент запуска.

**Почему в README нет количества доменов и бейджа релиза?**  
Текущие числа находятся в генерируемом `catalog.json`. На момент оформления репозиторий не использует опубликованные GitHub Releases, а статический счётчик в README быстро устаревал бы.

## Лицензия и контакты

В репозитории сейчас **нет файла LICENSE и не указана лицензия**. Не следует считать данные автоматически лицензированными для свободного копирования или распространения. Лицензия должна быть явно добавлена владельцем проекта после выбора подходящих условий.

- Сайт: [netlist.pro](https://netlist.pro)
- Предложить домен: [форма NetList](https://netlist.pro/submit-domain)
- Вопросы и ошибки: [GitHub Issues](https://github.com/Therealwh/NetList/issues/new)
- Изменения: [Pull Requests](https://github.com/Therealwh/NetList/pulls)

---

<sub>NetList — открытый каталог технических кандидатов. Проверяйте данные перед применением и не трактуйте DNS/IP-совпадение как доказательство владения или блокировки.</sub>
