# NetList

**Domain, IPv4, IPv6 and CIDR lists for network tools and routers.**

[![CI](https://github.com/Therealwh/NetList/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Therealwh/NetList/actions/workflows/ci.yml)
[![List updates](https://github.com/Therealwh/NetList/actions/workflows/update-lists.yml/badge.svg?branch=main)](https://github.com/Therealwh/NetList/actions/workflows/update-lists.yml)
![Formats](https://img.shields.io/badge/data-Domains%20%7C%20IPv4%20%7C%20IPv6%20%7C%20CIDR-536dfe)
[![Website](https://img.shields.io/badge/website-netlist.pro-2563eb?logo=googlechrome&logoColor=white)](https://netlist.pro)

**English** · [Русский](README.md)

> [!TIP]
> **Help keep the lists current.** Found a missing or outdated domain? Submit it through the [NetList suggestion form](https://netlist.pro/submit-domain). Every suggestion is reviewed before publication. By adding domains through the website, you help keep the shared datasets useful and up to date.

## Navigation

- [NetList website](https://netlist.pro) · [Browse lists](https://netlist.pro/lists) · [Categories](https://netlist.pro/categories)
- [Data catalog](catalog.json) · [Common lists](common/) · [Per-service lists](services/) · [Category collections](collections/)
- [Typed IP/CIDR lists](schemas/typed-lists.md) · [Catalog JSON Schema](schemas/catalog.schema.json) · [Source provenance](sources/seed/global/domain-sources.json)
- [GitHub Actions](https://github.com/Therealwh/NetList/actions) · [Report an issue](https://github.com/Therealwh/NetList/issues/new) · [Pull Requests](https://github.com/Therealwh/NetList/pulls)

## What is NetList?

NetList is a public repository of structured network data. It contains domains and DNS-derived IP snapshots grouped by service and topic. Files are published as UTF-8 TXT lists, with catalog metadata in JSON. They can be used as input for network rules, routing, DNS filtering and custom automation.

**NetList is not a universal ready-to-use blocklist.** Entries are candidates for technical configuration. Review which hosts and addresses are actually needed for your use case before applying them.

### NetList and routers

NetList can be used as a source of domain and IP/CIDR data when configuring routers and network-routing rules, provided the firmware and tooling support the relevant input format. The project owner also supplied this [4PDA router discussion (topic 1123087)](https://4pda.to/forum/index.php?showtopic=1123087). Check firmware compatibility, rule syntax and safe import size independently.

## Available data types

| Type | File | Meaning |
|---|---|---|
| Domains | `domains.txt` | Normalized domain names |
| IPv4 | `ipv4.txt` | Public IPv4 addresses resolved from DNS |
| IPv6 | `ipv6.txt` | Public IPv6 addresses resolved from DNS |
| CIDRv4 | `cidrv4.txt` | Exact IPv4 host routes using `/32` |
| CIDRv6 | `cidrv6.txt` | Exact IPv6 host routes using `/128` |

Common files are in [common/](common/); individual service files are in [services/](services/). Each service has its own directory, for example [VK](services/vk/), [Telegram](services/telegram/) or [YouTube](services/youtube/). Category collections live in [collections/](collections/) and currently contain aggregated domain lists.

### Common lists

| Dataset | Repository file | Raw URL |
|---|---|---|
| All domains | [common/domains.txt](common/domains.txt) | [Download](https://raw.githubusercontent.com/Therealwh/NetList/main/common/domains.txt) |
| IPv4 | [common/ipv4.txt](common/ipv4.txt) | [Download](https://raw.githubusercontent.com/Therealwh/NetList/main/common/ipv4.txt) |
| IPv6 | [common/ipv6.txt](common/ipv6.txt) | [Download](https://raw.githubusercontent.com/Therealwh/NetList/main/common/ipv6.txt) |
| CIDRv4 | [common/cidrv4.txt](common/cidrv4.txt) | [Download](https://raw.githubusercontent.com/Therealwh/NetList/main/common/cidrv4.txt) |
| CIDRv6 | [common/cidrv6.txt](common/cidrv6.txt) | [Download](https://raw.githubusercontent.com/Therealwh/NetList/main/common/cidrv6.txt) |
| JSON catalog | [catalog.json](catalog.json) | [Raw JSON](https://raw.githubusercontent.com/Therealwh/NetList/main/catalog.json) |

### Per-service examples

All five file types have been checked for the [VK](services/vk/) service:

- [VK domains](services/vk/domains.txt)
- [VK IPv4](services/vk/ipv4.txt)
- [VK IPv6](services/vk/ipv6.txt)
- [VK CIDRv4](services/vk/cidrv4.txt)
- [VK CIDRv6](services/vk/cidrv6.txt)

Raw service URLs follow this pattern:

`https://raw.githubusercontent.com/Therealwh/NetList/main/services/<slug>/<file>.txt`

Examples: `services/telegram/domains.txt` and `services/youtube/domains.txt`.

### Categories

Each link points to an existing `collections/<category>/domains.txt` file.

| Category | File |
|---|---|
| Adult 18+ | [adult_18](collections/adult_18/domains.txt) |
| Artificial intelligence | [ai](collections/ai/domains.txt) |
| Banks and payments | [banks_payments](collections/banks_payments/domains.txt) |
| Cloud and CDN | [cloud_cdn](collections/cloud_cdn/domains.txt) |
| Developer tools | [developer_tools](collections/developer_tools/domains.txt) |
| File sharing | [file_sharing](collections/file_sharing/domains.txt) |
| Finance and marketplaces | [finance_marketplaces](collections/finance_marketplaces/domains.txt) |
| Gambling | [gambling](collections/gambling/domains.txt) |
| Gaming | [gaming](collections/gaming/domains.txt) |
| Government | [government](collections/government/domains.txt) |
| Health and sport | [health_sport](collections/health_sport/domains.txt) |
| IT, business and education | [it_business_education](collections/it_business_education/domains.txt) |
| Mail | [mail](collections/mail/domains.txt) |
| Marketplaces and delivery | [marketplaces_delivery](collections/marketplaces_delivery/domains.txt) |
| Messengers | [messengers](collections/messengers/domains.txt) |
| Telecom | [messengers_telecom](collections/messengers_telecom/domains.txt) |
| Movies | [movies](collections/movies/domains.txt) |
| Music | [music](collections/music/domains.txt) |
| News and education | [news_education](collections/news_education/domains.txt) |
| Operating systems and security | [os_security](collections/os_security/domains.txt) |
| Search ecosystems | [search_ecosystems](collections/search_ecosystems/domains.txt) |
| Search portals | [search_portals](collections/search_portals/domains.txt) |
| Social networks | [social](collections/social/domains.txt) |
| Torrents and P2P | [torrents_p2p](collections/torrents_p2p/domains.txt) |
| Transport | [transport](collections/transport/domains.txt) |
| Video, music and media | [video_music_media](collections/video_music_media/domains.txt) |
| Video streaming | [video_streaming](collections/video_streaming/domains.txt) |

## Quick start

### Download with curl

Linux, macOS or a router with `curl`:

```bash
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/common/domains.txt" -o domains.txt
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/common/ipv4.txt" -o ipv4.txt
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/common/ipv6.txt" -o ipv6.txt
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/common/cidrv4.txt" -o cidrv4.txt
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/common/cidrv6.txt" -o cidrv6.txt
```

Download one service:

```bash
curl -fL "https://raw.githubusercontent.com/Therealwh/NetList/main/services/vk/domains.txt" -o vk-domains.txt
```

### Download with PowerShell

```powershell
$base = "https://raw.githubusercontent.com/Therealwh/NetList/main/common"
Invoke-WebRequest "$base/domains.txt" -OutFile ".\domains.txt"
Invoke-WebRequest "$base/ipv4.txt" -OutFile ".\ipv4.txt"
Invoke-WebRequest "$base/ipv6.txt" -OutFile ".\ipv6.txt"
Invoke-WebRequest "$base/cidrv4.txt" -OutFile ".\cidrv4.txt"
Invoke-WebRequest "$base/cidrv6.txt" -OutFile ".\cidrv6.txt"
```

### Raw GitHub URLs

Read files directly without cloning:

```text
https://raw.githubusercontent.com/Therealwh/NetList/main/<path>
```

Replace `<path>` with an actual path, such as `common/domains.txt`, `collections/social/domains.txt` or `services/telegram/ipv4.txt`. The URL targets `main`, so new published content becomes available at the same address. For reproducible builds, pin a commit SHA instead.

## Catalog and documentation

- [catalog.json](catalog.json) — schema version, generation time, counts, categories and service records.
- [JSON Schema](schemas/catalog.schema.json) — catalog structure.
- [Typed lists](schemas/typed-lists.md) — how IP and CIDR files are generated.
- [Domain source provenance](sources/seed/global/domain-sources.json) — selected source references and explanations.
- [Global seed](sources/seed/global/) · [Russian seed](sources/seed/russian/) · [User submissions](sources/user_submissions/).

For current service, category and domain counts, read the generated `catalog.json`. Counts are produced by the builder, so this README deliberately avoids manually maintained numbers.

## How the data is built

1. **Seed and registry.** Initial datasets live in `sources/seed/global/` and `sources/seed/russian/`; the service registry is stored in `state/registry.json`. Selected source references are recorded in `sources/seed/global/domain-sources.json`.
2. **Community submissions.** Suggestions reviewed by the website moderator are stored in `sources/user_submissions/` and included in subsequent builds. A suggestion is not proof that a domain belongs to a service.
3. **Normalization.** Domains are lowercased and converted to ASCII/IDNA (punycode). Invalid names, wildcard entries, localhost and unsuitable values are discarded. IP addresses and CIDRs are canonicalized with Python's `ipaddress` module.
4. **Deduplication.** Entries are normalized, sorted and deduplicated within service and category sets. A domain may be associated with more than one service, so it can appear in multiple groups in the grouped `common/domains.txt`.
5. **DNS snapshots.** The update job resolves domains through the system DNS resolver and creates public IPv4/IPv6 lists. CIDRv4/CIDRv6 files contain exact `/32` and `/128` host routes for those addresses; they are not claims of ownership over an address range.
6. **Data-loss protection.** If DNS temporarily returns no addresses for a service, its previous snapshot is retained. Guard checks stop publication when the output is empty or the overall/service data drops sharply.
7. **Publishing.** The workflow stages only explicitly allowed generated paths. It does not create an empty commit when there are no content changes.

The daily workflow rebuilds the tracked registry and community submissions and refreshes DNS snapshots. It is not a general internet crawler and does not automatically download every external seed source.

## Automated updates and validation

| Workflow | Purpose |
|---|---|
| [update-lists.yml](.github/workflows/update-lists.yml) | Build, DNS snapshots, guard checks and publishing |
| [ci.yml](.github/workflows/ci.yml) | Structure checks, unit tests, catalog build and data-loss guards |

- **Schedule:** daily at 03:00 UTC.
- **Manual run:** GitHub → Actions → **update-lists** → **Run workflow** → select branch `main`.
- **CI:** runs on Pull Requests, pushes to `main` and manual dispatch.
- **Runtime:** Python 3.12 and the Python standard library.
- **Protection:** the guard blocks an empty output or suspicious total/per-service reductions; a failed guard prevents the workflow from publishing the new dataset.
- **Commit scope:** the workflow does not use an unconditional `git add -A`; only explicitly allowed data and generated paths are staged.

See current runs in [GitHub Actions](https://github.com/Therealwh/NetList/actions).

## Contributing

1. Open the [domain suggestion form](https://netlist.pro/submit-domain).
2. Provide the domain and, if useful, service name, category and source URL.
3. Wait for moderator review. Do not submit passwords, tokens, private addresses or confidential information.
4. To correct a published entry, open a [GitHub Issue](https://github.com/Therealwh/NetList/issues/new) with the file path and supporting information, or submit a Pull Request.

Suggestions are not added to the public catalog automatically. They provide material for maintainer review.

## Accuracy and limitations

- A domain's presence in NetList **does not prove that it is blocked**, unavailable or required by a service.
- DNS answers change. Published IPs are snapshots from the last successful resolution.
- A single IP may serve unrelated websites through a CDN, reverse proxy or shared hosting. It does not necessarily belong to the named service.
- Current CIDR outputs represent exact host routes (`/32` or `/128`), not a provider's full network ranges.
- Lists may be incomplete, stale or disputed and must be checked for the specific firmware, app and network task.
- Treat these files as technical starting points, not as a guarantee of availability or accuracy.

## FAQ

**Is this a ready-made blocklist?**  
No. It is a set of candidates for network configuration. Review each entry before use.

**Why can an IP appear more than once?**  
The same address may be returned for several domains or shared by a CDN/hosting provider. Repeats between labelled groups are intentional.

**Why are CIDRs `/32` and `/128`?**  
They represent one IPv4 or IPv6 address as an exact host route. They do not indicate that NetList discovered an entire service subnet.

**Can I use the lists on a router?**  
Yes, when its firmware supports importing or converting TXT domain, IP and host-route lists. Supported syntax and routing behavior depend on the router software.

**How often are lists updated?**  
The workflow runs daily at 03:00 UTC, on pushes to `main` and manually. DNS snapshots depend on resolver availability and answers at run time.

**Why is there no license or release badge?**  
There is no LICENSE file and no GitHub Release currently published. No license is assumed, and a static count or release badge would be misleading.

## License and contact

There is currently **no LICENSE file and no declared license** in this repository. Do not assume that the data is automatically licensed for unrestricted copying or redistribution. The project owner must add an explicit license after choosing its terms.

- Website: [netlist.pro](https://netlist.pro)
- Suggest a domain: [NetList form](https://netlist.pro/submit-domain)
- Questions and bug reports: [GitHub Issues](https://github.com/Therealwh/NetList/issues/new)
- Contributions: [Pull Requests](https://github.com/Therealwh/NetList/pulls)

---

<sub>NetList is a catalog of technical candidates. Validate entries before use; a DNS/IP match is not proof of ownership or blocking.</sub>
