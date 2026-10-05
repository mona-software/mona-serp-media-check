"""Cac ham tai du lieu qua mang, tach rieng de test co the mock/inject.

Moi ham nhan them tham so `opener` (mac dinh None -> dung urllib chuan)
de test co the thay the bang mot ham gia lap, tranh goi mang that.
"""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

DEFAULT_TIMEOUT = 10
USER_AGENT = (
    "Mozilla/5.0 (compatible; mona-serp-media-check/0.1; "
    "+https://github.com/mona-software/mona-serp-media-check)"
)


@dataclass
class FetchResult:
    ok: bool
    status: int | None
    data: bytes | None
    content_type: str = ""
    error: str = ""


def _default_opener(url: str, timeout: int) -> FetchResult:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            return FetchResult(
                ok=True,
                status=resp.status,
                data=data,
                content_type=resp.headers.get("Content-Type", ""),
            )
    except urllib.error.HTTPError as exc:
        return FetchResult(ok=False, status=exc.code, data=None, error=str(exc))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return FetchResult(ok=False, status=None, data=None, error=str(exc))


def fetch(url: str, timeout: int = DEFAULT_TIMEOUT, opener=None) -> FetchResult:
    fn = opener or _default_opener
    return fn(url, timeout)


def fetch_text(url: str, timeout: int = DEFAULT_TIMEOUT, opener=None) -> str | None:
    result = fetch(url, timeout=timeout, opener=opener)
    if not result.ok or result.data is None:
        return None
    try:
        return result.data.decode("utf-8", errors="replace")
    except Exception:
        return result.data.decode("latin-1", errors="replace")


def resolve_url(base: str, maybe_relative: str) -> str:
    """Ghep URL tuong doi voi base. Neu da la URL tuyet doi thi giu nguyen."""
    if not maybe_relative:
        return maybe_relative
    parsed = urlparse(maybe_relative)
    if parsed.scheme and parsed.netloc:
        return maybe_relative
    if not base:
        return maybe_relative
    return urljoin(base, maybe_relative)


def guess_sitemap_urls(base_domain: str) -> list[str]:
    base_domain = base_domain.rstrip("/")
    if not base_domain.startswith("http"):
        base_domain = "https://" + base_domain
    return [
        f"{base_domain}/page-sitemap.xml",
        f"{base_domain}/sitemap.xml",
    ]


def guess_video_sitemap_urls(base_domain: str) -> list[str]:
    base_domain = base_domain.rstrip("/")
    if not base_domain.startswith("http"):
        base_domain = "https://" + base_domain
    return [
        f"{base_domain}/video-sitemap.xml",
    ]
