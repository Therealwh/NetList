"""Нормализация и валидация сетевых записей NetList. Только stdlib."""
from __future__ import annotations

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
