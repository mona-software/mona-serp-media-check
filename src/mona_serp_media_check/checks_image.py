"""Kiem tra nhom ANH: alt text, ten file, schema ImageObject, kich thuoc that,
va doi chieu voi image sitemap.

Trong bo checklist nay, mot "anh noi dung" la anh nam trong vung noi
dung chinh cua trang (uu tien <main>/<article> neu co, de loai anh
khung chung nhu logo header/footer lap lai o moi trang). Anh trang tri
(icon/arrow/bg/logo/decor/spinner/pattern trong ten file) duoc mien
kiem alt NEU danh dau ro rang bang aria-hidden="true" hoac
role="presentation" -- day la cach danh dau chuan de noi voi trinh doc
man hinh (va voi cong cu nay) rang anh khong mang thong tin.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

from . import fetch as fetch_mod
from . import image_dims
from . import jsonld
from .htmlparse import PageIndex
from .models import Finding
from .textutil import (
    filename_matches_keyword,
    filename_meaningful_words,
    filename_stem,
    has_vietnamese_diacritics,
    word_count,
)

DECOR_FILENAME_PATTERN = re.compile(
    r"(icon|arrow|\bbg\b|background|logo|decor|spinner|pattern)", re.IGNORECASE
)
ENGLISH_MEANINGLESS_ALT = {"image", "photo", "picture", "img"}
MIN_ALT_WORDS = 6
MAX_ALT_WORDS = 20
MIN_KEYWORD_IMAGES = 3
MIN_CAPTIONED_IMAGE_OBJECTS = 3
MIN_WIDE_IMAGE_PX = 1200
IMAGES_TO_DOWNLOAD_FOR_DIMS = 2


def _content_images(page: PageIndex):
    if page.has_main_region:
        return [img for img in page.imgs if img.in_main]
    return [img for img in page.imgs if not img.in_chrome]


def _is_svg(src: str) -> bool:
    return src.lower().split("?")[0].endswith(".svg")


def _is_decorative(src: str, attrs: dict) -> bool:
    stem = filename_stem(src)
    looks_decor = bool(DECOR_FILENAME_PATTERN.search(stem))
    marked_decorative = (
        attrs.get("aria-hidden", "").strip().lower() == "true"
        or attrs.get("role", "").strip().lower() == "presentation"
    )
    return looks_decor and marked_decorative


def run(
    page: PageIndex,
    keyword: str,
    base_url: str = "",
    fast: bool = True,
    fetcher=None,
) -> list[Finding]:
    findings: list[Finding] = []
    content_imgs = _content_images(page)
    lang = (page.lang or "").strip().lower()

    alt_to_srcs: dict[str, set[str]] = {}
    keyword_match_count = 0
    resolved_content_srcs: set[str] = set()

    for img in content_imgs:
        src = img.attrs.get("src", "") or img.attrs.get("data-src", "")
        if not src:
            continue
        resolved = fetch_mod.resolve_url(base_url, src) if base_url else src
        resolved_content_srcs.add(resolved)

        has_real_src = bool(img.attrs.get("src"))
        has_lazy_only = (not has_real_src) and bool(img.attrs.get("data-src"))
        if has_lazy_only:
            findings.append(
                Finding(
                    "fail",
                    "image",
                    "IMG_LAZY_ONLY",
                    f"Anh chi co data-src, thieu src that: {src} "
                    "(cong cu tim kiem co the khong doc duoc).",
                )
            )

        is_svg = _is_svg(src)
        is_decor = _is_decorative(src, img.attrs)
        alt = (img.attrs.get("alt") or "").strip()

        if filename_matches_keyword(filename_stem(src), keyword):
            keyword_match_count += 1

        if not is_decor and not is_svg:
            stem = filename_stem(src)
            meaningful_words = filename_meaningful_words(stem)
            if len(meaningful_words) < 3:
                findings.append(
                    Finding(
                        "fail",
                        "image",
                        "IMG_FILENAME_MEANINGLESS",
                        f"Ten file anh chua co nghia ro rang: {src} "
                        "(tach theo -/_ duoc it hon 3 tu khong phai so).",
                    )
                )

            if not alt:
                findings.append(
                    Finding(
                        "fail",
                        "image",
                        "IMG_ALT_MISSING",
                        f"Anh thieu alt text: {src}",
                    )
                )
            else:
                alt_to_srcs.setdefault(alt, set()).add(resolved)
                n_words = word_count(alt)
                if n_words < MIN_ALT_WORDS or n_words > MAX_ALT_WORDS:
                    findings.append(
                        Finding(
                            "warn",
                            "image",
                            "IMG_ALT_LENGTH",
                            f"Alt cua {src} co {n_words} tu, nen trong khoang "
                            f"{MIN_ALT_WORDS}-{MAX_ALT_WORDS} tu de mo ta du ma khong nhoi nhet.",
                        )
                    )
                if lang == "vi" and not has_vietnamese_diacritics(alt):
                    findings.append(
                        Finding(
                            "warn",
                            "image",
                            "IMG_ALT_NO_DIACRITICS",
                            f"Trang khai lang=vi nhung alt cua {src} khong co dau tieng Viet: '{alt}'",
                        )
                    )
                if lang == "en" and alt.strip().lower() in ENGLISH_MEANINGLESS_ALT:
                    findings.append(
                        Finding(
                            "warn",
                            "image",
                            "IMG_ALT_MEANINGLESS_EN",
                            f"Alt cua {src} chi la mot tu chung chung: '{alt}'",
                        )
                    )

    for alt, srcs in alt_to_srcs.items():
        if len(srcs) > 1:
            findings.append(
                Finding(
                    "fail",
                    "image",
                    "IMG_ALT_DUPLICATE",
                    f"Alt '{alt}' bi dung trung cho {len(srcs)} file anh khac nhau.",
                )
            )

    if keyword_match_count < MIN_KEYWORD_IMAGES:
        findings.append(
            Finding(
                "fail",
                "image",
                "IMG_KEYWORD_FILENAME",
                f"Chi co {keyword_match_count} anh co ten file chua tu khoa "
                f"'{keyword}', can toi thieu {MIN_KEYWORD_IMAGES} anh.",
            )
        )

    findings.extend(_check_image_object_schema(page, base_url, resolved_content_srcs))

    if not fast:
        findings.extend(_check_real_dimensions(content_imgs, base_url, fetcher))
        if base_url:
            findings.extend(
                _check_sitemap_orphans(base_url, resolved_content_srcs, fetcher)
            )

    return findings


def _check_image_object_schema(
    page: PageIndex, base_url: str, resolved_content_srcs: set[str]
) -> list[Finding]:
    findings: list[Finding] = []
    parsed_blocks, parse_errors = jsonld.parse_blocks(page.ld_json_blocks)
    for err in parse_errors:
        findings.append(
            Finding("fail", "image", "JSONLD_PARSE_ERROR", f"Loi cu phap JSON-LD: {err}")
        )

    image_objects = jsonld.nodes_of_type(parsed_blocks, "ImageObject")

    captioned = [node for node in image_objects if str(node.get("caption") or "").strip()]
    if len(captioned) < MIN_CAPTIONED_IMAGE_OBJECTS:
        findings.append(
            Finding(
                "fail",
                "image",
                "IMAGEOBJECT_CAPTION_COUNT",
                f"Chi co {len(captioned)} khoi ImageObject co 'caption', "
                f"can toi thieu {MIN_CAPTIONED_IMAGE_OBJECTS}.",
            )
        )

    for node in image_objects:
        declared = node.get("contentUrl") or node.get("url") or ""
        if not declared:
            continue
        resolved_declared = fetch_mod.resolve_url(base_url, declared) if base_url else declared
        if resolved_content_srcs and resolved_declared not in resolved_content_srcs:
            findings.append(
                Finding(
                    "fail",
                    "image",
                    "IMAGEOBJECT_ORPHAN",
                    f"ImageObject khai anh '{declared}' nhung khong thay anh nay "
                    "that su xuat hien tren trang.",
                )
            )

        missing_rights_fields = [
            field
            for field in ("creator", "creditText", "copyrightNotice")
            if not node.get(field)
        ]
        if missing_rights_fields:
            findings.append(
                Finding(
                    "warn",
                    "image",
                    "IMAGEOBJECT_RIGHTS_INCOMPLETE",
                    f"ImageObject '{declared or '(khong ro URL)'}' thieu truong "
                    f"ban quyen: {', '.join(missing_rights_fields)}.",
                )
            )

    return findings


def _check_real_dimensions(content_imgs, base_url: str, fetcher) -> list[Finding]:
    findings: list[Finding] = []
    candidates = []
    for img in content_imgs:
        src = img.attrs.get("src", "")
        if src and not _is_svg(src):
            candidates.append(src)
        if len(candidates) >= IMAGES_TO_DOWNLOAD_FOR_DIMS:
            break

    if not candidates:
        return findings

    found_wide_image = False
    downloaded = 0
    for src in candidates:
        url = fetch_mod.resolve_url(base_url, src) if base_url else src
        if not url.startswith("http"):
            continue
        result = fetch_mod.fetch(url, opener=fetcher)
        if not result.ok or not result.data:
            continue
        downloaded += 1
        dims = image_dims.get_image_dimensions(result.data)
        if dims and dims[0] >= MIN_WIDE_IMAGE_PX:
            found_wide_image = True

    if downloaded > 0 and not found_wide_image:
        findings.append(
            Finding(
                "warn",
                "image",
                "IMG_TOO_SMALL",
                f"Khong co anh chu luc nao rong >= {MIN_WIDE_IMAGE_PX}px "
                "(Google Images uu tien anh do phan giai cao).",
            )
        )
    return findings


_XML_NS = {"image": "http://www.google.com/schemas/sitemap-image/1.1"}


def _check_sitemap_orphans(base_url: str, resolved_content_srcs: set[str], fetcher) -> list[Finding]:
    findings: list[Finding] = []
    domain = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}" if "://" in base_url else base_url
    sitemap_urls = fetch_mod.guess_sitemap_urls(domain)

    for sitemap_url in sitemap_urls:
        result = fetch_mod.fetch(sitemap_url, opener=fetcher)
        if not result.ok or not result.data:
            continue
        try:
            root = ET.fromstring(result.data)
        except ET.ParseError:
            continue

        for url_node in root.iter():
            if not url_node.tag.endswith("}url") and url_node.tag != "url":
                continue
            loc_node = None
            image_locs = []
            for child in url_node:
                tag = child.tag.rsplit("}", 1)[-1]
                if tag == "loc" and loc_node is None:
                    loc_node = child
                if tag == "image":
                    for gchild in child:
                        gtag = gchild.tag.rsplit("}", 1)[-1]
                        if gtag == "loc":
                            image_locs.append((gchild.text or "").strip())

            page_loc = (loc_node.text or "").strip() if loc_node is not None else ""
            if not page_loc or page_loc.rstrip("/") != base_url.rstrip("/"):
                continue
            for image_loc in image_locs:
                if image_loc and image_loc not in resolved_content_srcs:
                    findings.append(
                        Finding(
                            "warn",
                            "image",
                            "SITEMAP_IMAGE_ORPHAN",
                            f"Sitemap khai anh '{image_loc}' cho trang nay nhung khong "
                            "thay anh do tren trang that.",
                        )
                    )
        break  # chi can 1 sitemap doc duoc la du, khong thu tiep file khac
    return findings
