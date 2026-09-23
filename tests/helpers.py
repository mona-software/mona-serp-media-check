"""Tien ich dung chung cho test: fixture HTML + fake fetcher (khong goi mang)."""

from __future__ import annotations

import struct
import zlib

from mona_serp_media_check.fetch import FetchResult

BASE_URL = "https://example.vn/bai-viet-mau"


def wrap_html(body: str, lang: str = "vi", head_extra: str = "") -> str:
    return f"""<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<title>Bai viet mau</title>
{head_extra}
</head>
<body>
{body}
</body>
</html>"""


def make_fake_fetcher(responses: dict[str, bytes]):
    """Tra ve mot ham opener(url, timeout) -> FetchResult tu dict co san,
    de test khong bao gio goi mang that."""

    def _opener(url: str, timeout: int) -> FetchResult:
        if url in responses:
            return FetchResult(ok=True, status=200, data=responses[url], content_type="")
        return FetchResult(ok=False, status=404, data=None, error="not found (fake)")

    return _opener


def failing_fetcher(url: str, timeout: int) -> FetchResult:
    raise AssertionError(f"Khong duoc goi mang trong che do --fast: {url}")


def make_png(width: int, height: int) -> bytes:
    """Tao mot file PNG hop le voi kich thuoc bat ky, dung de test doc header."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw_row = b"\x00" + b"\xff\x00\x00\xff" * width
    raw = raw_row * height
    idat = zlib.compress(raw)
    return signature + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


# Anh PNG 1x1 hop le nho nhat, dung de test doc kich thuoc that.
PNG_1X1 = make_png(1, 1)
