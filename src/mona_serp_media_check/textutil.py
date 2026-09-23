"""Ham xu ly chuoi dung chung: bo dau, tach tu, nhan dien tieng Viet co dau."""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import unquote, urlparse

_VN_EXTRA_CHARS = set("đĐ")


def strip_diacritics(text: str) -> str:
    """Bo dau tieng Viet, giu lai chu cai/so, dung de so khop khong dau."""
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    without_marks = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", without_marks)


def has_vietnamese_diacritics(text: str) -> bool:
    """True neu chuoi co it nhat 1 ky tu dau tieng Viet (khac ASCII)."""
    for ch in text:
        if ch in _VN_EXTRA_CHARS:
            return True
        normalized = unicodedata.normalize("NFD", ch)
        if any(unicodedata.category(c) == "Mn" for c in normalized):
            return True
    return False


def word_count(text: str) -> int:
    return len([w for w in re.split(r"\s+", text.strip()) if w])


def filename_from_url(url_or_path: str) -> str:
    path = urlparse(url_or_path).path or url_or_path
    name = path.rsplit("/", 1)[-1]
    return unquote(name)


def filename_stem(url_or_path: str) -> str:
    name = filename_from_url(url_or_path)
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return name


def filename_meaningful_words(stem: str) -> list[str]:
    """Tach ten file theo '-'/'_', chi giu tu KHONG phai toan so."""
    parts = re.split(r"[-_]+", stem)
    return [p for p in parts if p and not p.isdigit()]


def normalize_ascii_lower(text: str) -> str:
    return strip_diacritics(text).lower()


def keyword_words(keyword: str, min_len: int = 3) -> list[str]:
    normalized = normalize_ascii_lower(keyword)
    tokens = re.split(r"[^a-z0-9]+", normalized)
    return [t for t in tokens if len(t) >= min_len]


def filename_matches_keyword(stem: str, keyword: str) -> bool:
    normalized_stem = normalize_ascii_lower(stem)
    for word in keyword_words(keyword):
        if word in normalized_stem:
            return True
    return False
