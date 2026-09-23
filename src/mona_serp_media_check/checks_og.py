"""Kiem tra nhom OPEN GRAPH IMAGE (anh dai dien khi chia se link)."""

from __future__ import annotations

import re

from . import fetch as fetch_mod
from .htmlparse import PageIndex
from .models import Finding
from .textutil import filename_matches_keyword, filename_stem

# Cac pattern ten file THUONG GAP cho anh dung chung/mac dinh, khong
# gan voi noi dung cu the cua tung trang. Viet o dang tong quat, khong
# gan cung ten thuong hieu nao.
GENERIC_OG_PATTERN = re.compile(
    r"(default|placeholder|banner|fallback|generic|share[-_]?image|og[-_]?image)",
    re.IGNORECASE,
)

MIN_OG_DESC_LEN = 20
OG_WIDTH_TARGET = 1200
OG_HEIGHT_TARGET = 630
OG_RATIO_MIN = 1.7
OG_RATIO_MAX = 2.1
MIN_OG_IMAGE_BYTES = 5 * 1024


def _get_meta(page: PageIndex, prop_names: tuple[str, ...]) -> str:
    for meta in page.metas:
        key = meta.get("property") or meta.get("name") or ""
        if key.lower() in prop_names:
            return meta.get("content", "")
    return ""


def run(
    page: PageIndex,
    keyword: str,
    page_url: str = "",
    base_url: str = "",
    fast: bool = True,
    fetcher=None,
) -> list[Finding]:
    findings: list[Finding] = []

    og_image = _get_meta(page, ("og:image", "og:image:secure_url"))
    if not og_image:
        findings.append(
            Finding("fail", "og", "OG_IMAGE_MISSING", "Trang khong khai the og:image.")
        )
        return findings

    stem = filename_stem(og_image)
    if GENERIC_OG_PATTERN.search(stem):
        findings.append(
            Finding(
                "warn",
                "og",
                "OG_IMAGE_GENERIC",
                f"Ten file og:image trong giong anh dung chung/mac dinh: {og_image}",
            )
        )

    slug = ""
    if page_url:
        slug = page_url.rstrip("/").rsplit("/", 1)[-1]
    matches_keyword = filename_matches_keyword(stem, keyword)
    matches_slug = bool(slug) and filename_matches_keyword(stem, slug.replace("-", " "))
    if not matches_keyword and not matches_slug:
        findings.append(
            Finding(
                "warn",
                "og",
                "OG_IMAGE_NOT_SPECIFIC",
                f"Ten file og:image ({og_image}) khong chua tu khoa hay slug cua trang.",
            )
        )

    og_width = _get_meta(page, ("og:image:width",))
    og_height = _get_meta(page, ("og:image:height",))
    if not og_width or not og_height:
        findings.append(
            Finding(
                "warn",
                "og",
                "OG_IMAGE_DIMENSIONS_MISSING",
                "Thieu og:image:width/og:image:height (giup mang xa hoi render nhanh, khong bi giat layout).",
            )
        )

    og_title = _get_meta(page, ("og:title",))
    og_desc = _get_meta(page, ("og:description",))
    if not og_title:
        findings.append(Finding("warn", "og", "OG_TITLE_MISSING", "Thieu the og:title."))
    if not og_desc or len(og_desc.strip()) <= MIN_OG_DESC_LEN:
        findings.append(
            Finding(
                "warn",
                "og",
                "OG_DESCRIPTION_SHORT",
                f"og:description qua ngan hoac thieu (can > {MIN_OG_DESC_LEN} ky tu).",
            )
        )

    if not fast:
        resolved = fetch_mod.resolve_url(base_url or page_url, og_image)
        if resolved.startswith("http"):
            result = fetch_mod.fetch(resolved, opener=fetcher)
            if not result.ok or not result.data:
                findings.append(
                    Finding(
                        "fail",
                        "og",
                        "OG_IMAGE_UNREACHABLE",
                        f"Khong tai duoc og:image tu {resolved}.",
                    )
                )
            else:
                if len(result.data) < MIN_OG_IMAGE_BYTES:
                    findings.append(
                        Finding(
                            "warn",
                            "og",
                            "OG_IMAGE_TOO_SMALL_FILESIZE",
                            f"og:image chi nang {len(result.data)} byte, co the la anh loi/rong.",
                        )
                    )
                from . import image_dims

                dims = image_dims.get_image_dimensions(result.data)
                if dims:
                    width, height = dims
                    ratio = width / height if height else 0
                    if ratio < OG_RATIO_MIN or ratio > OG_RATIO_MAX:
                        findings.append(
                            Finding(
                                "warn",
                                "og",
                                "OG_IMAGE_RATIO_OFF",
                                f"og:image kich thuoc {width}x{height} (ty le {ratio:.2f}) "
                                f"lech chuan ~{OG_WIDTH_TARGET}x{OG_HEIGHT_TARGET} (ty le ~1.91).",
                            )
                        )

    return findings
