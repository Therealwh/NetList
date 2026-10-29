"""Нормализация и валидация сетевых записей NetList. Только stdlib."""
from __future__ import annotations

import ipaddress
import re
import unicodedata

# Практическая транслитерация кириллицы: 'Хабр'->habr, 'Одноклассники'->odnoklassniki
TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

# Брендовые написания вместо буквальной транслитерации ('yandeks', '1s')
_BRAND_SUBSTRINGS = (("яндекс", "yandex"), ("1с", "1c"))


def slugify(name: str) -> str:
    """Имя сервиса -> слаг каталога. Пустой результат — ValueError."""
    text = unicodedata.normalize("NFKC", name).strip().lower()
    for cyrillic, latin in _BRAND_SUBSTRINGS:
        text = text.replace(cyrillic, latin)
    parts: list[str] = []
    for ch in text:
        if ch in TRANSLIT:
            parts.append(TRANSLIT[ch])
        elif "a" <= ch <= "z" or "0" <= ch <= "9":
            parts.append(ch)
        else:
            parts.append("-")
    slug = re.sub(r"-{2,}", "-", "".join(parts)).strip("-")
    if not slug:
        raise ValueError(f"cannot slugify name: {name!r}")
    return slug


_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$")


def normalize_domain(raw: str) -> str | None:
    """Канонический ASCII-домен (IDN -> punycode) или None.

    Отбрасывает схему/путь/порт/userinfo, '*'-шаблоны, localhost и некорректные имена.
    """
    value = unicodedata.normalize("NFKC", raw).strip().lower()
    if not value or "*" in value or " " in value:
        return None
    if "://" in value:
        value = value.split("://", 1)[1]
    value = value.split("/", 1)[0].rsplit("@", 1)[-1].split(":", 1)[0]
    value = value.rstrip(".")
    if not value or value == "localhost" or value.endswith(".local"):
        return None
    try:
        ascii_value = value.encode("idna").decode("ascii").lower()
    except UnicodeError:
        return None
    labels = ascii_value.split(".")
    if len(labels) < 2 or any(not _LABEL_RE.match(label) for label in labels):
        return None
    return ascii_value


def normalize_ip(raw: str) -> str | None:
    try:
        return ipaddress.ip_address(raw.strip()).compressed
    except ValueError:
        return None


def normalize_cidr(raw: str) -> tuple[str, int] | None:
    """Явный CIDR ('a.b.c.d/nn') -> (нормализованная сеть, версия). IP без '/' не CIDR."""
    value = raw.strip()
    if "/" not in value:
        return None
    try:
        network = ipaddress.ip_network(value, strict=False)
    except ValueError:
        return None
    return network.compressed, network.version
