"""Kiem tra nhom VIDEO: co video khong, schema VideoObject, transcript,
va cac tin hieu ngu canh (chu bao quanh, sitemap video).

Video la loai noi dung "co thi tot, khong co thi thoi" -- khong phai
trang nao cung can nhung neu da co video ma thieu du lieu co cau truc
thi coi nhu bo lo co hoi len khoi video cua SERP.
"""

from __future__ import annotations

from . import fetch as fetch_mod
from . import jsonld
from .htmlparse import PageIndex
from .models import Finding
from .textutil import keyword_words, normalize_ascii_lower

MIN_TRANSCRIPT_CHARS = 200
MIN_SURROUNDING_WORDS = 300
REQUIRED_VIDEOOBJECT_FIELDS = ("name", "description", "thumbnailUrl", "uploadDate", "duration")


def run(
    page: PageIndex,
    keyword: str,
    base_url: str = "",
    fast: bool = True,
    fetcher=None,
) -> list[Finding]:
    findings: list[Finding] = []

    if not page.videos:
        findings.append(
            Finding(
                "warn",
                "video",
                "VIDEO_ABSENT",
                "Trang khong co video nao (khong bat buoc, nhung neu chu de "
                "phu hop thi video se giup len khoi video cua SERP).",
            )
        )
        return findings

    parsed_blocks, parse_errors = jsonld.parse_blocks(page.ld_json_blocks)
    for err in parse_errors:
        findings.append(
            Finding("fail", "video", "JSONLD_PARSE_ERROR", f"Loi cu phap JSON-LD: {err}")
        )

    video_objects = jsonld.nodes_of_type(parsed_blocks, "VideoObject")
    if not video_objects:
        findings.append(
            Finding(
                "warn",
                "video",
                "VIDEOOBJECT_MISSING",
                "Trang co video nhung khong co schema VideoObject (JSON-LD).",
            )
        )
    else:
        for node in video_objects:
            missing = [f for f in REQUIRED_VIDEOOBJECT_FIELDS if not node.get(f)]
            if missing:
                findings.append(
                    Finding(
                        "warn",
                        "video",
                        "VIDEOOBJECT_FIELDS_MISSING",
                        f"VideoObject thieu truong: {', '.join(missing)}.",
                    )
                )

            name = normalize_ascii_lower(str(node.get("name") or ""))
            kw_words = keyword_words(keyword)
            if kw_words and not any(w in name for w in kw_words):
                findings.append(
                    Finding(
                        "warn",
                        "video",
                        "VIDEOOBJECT_NAME_NO_KEYWORD",
                        f"Ten VideoObject ('{node.get('name')}') khong chua tu khoa chinh '{keyword}'.",
                    )
                )

            transcript = str(node.get("transcript") or "")
            if len(transcript.strip()) <= MIN_TRANSCRIPT_CHARS:
                findings.append(
                    Finding(
                        "warn",
                        "video",
                        "VIDEO_TRANSCRIPT_MISSING",
                        "VideoObject khong co transcript du dai (>200 ky tu) -- day la tin hieu "
                        "manh de Google hieu noi dung video noi ve gi.",
                    )
                )

            if not node.get("potentialAction"):
                findings.append(
                    Finding(
                        "warn",
                        "video",
                        "VIDEO_NO_SEEK_ACTION",
                        "VideoObject khong khai potentialAction (SeekToAction) nen kho len "
                        "muc 'khoanh khac quan trong' trong ket qua video.",
                    )
                )

            if not fast:
                thumb = node.get("thumbnailUrl")
                if isinstance(thumb, list):
                    thumb = thumb[0] if thumb else ""
                if thumb:
                    resolved = fetch_mod.resolve_url(base_url, thumb) if base_url else thumb
                    if resolved.startswith("http"):
                        result = fetch_mod.fetch(resolved, opener=fetcher)
                        if not result.ok:
                            findings.append(
                                Finding(
                                    "fail",
                                    "video",
                                    "VIDEO_THUMBNAIL_UNREACHABLE",
                                    f"Khong tai duoc thumbnailUrl cua video: {resolved}",
                                )
                            )

    if page.total_word_count < MIN_SURROUNDING_WORDS:
        findings.append(
            Finding(
                "warn",
                "video",
                "VIDEO_CONTEXT_TEXT_THIN",
                f"Trang chi co khoang {page.total_word_count} tu, nen co toi thieu "
                f"{MIN_SURROUNDING_WORDS} tu de Google tin video khop chu de trang.",
            )
        )

    if not fast and base_url:
        findings.extend(_check_video_sitemap(base_url, fetcher))

    return findings


def _check_video_sitemap(base_url: str, fetcher) -> list[Finding]:
    findings: list[Finding] = []
    from urllib.parse import urlparse

    domain = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}" if "://" in base_url else base_url
    for sitemap_url in fetch_mod.guess_video_sitemap_urls(domain):
        result = fetch_mod.fetch(sitemap_url, opener=fetcher)
        if result.ok and result.data:
            return findings  # co file, khong can canh bao them o day
    findings.append(
        Finding(
            "warn",
            "video",
            "VIDEO_SITEMAP_MISSING",
            "Khong tim thay video-sitemap.xml (khong bat buoc, nhung giup Google "
            "kham pha video nhanh hon).",
        )
    )
    return findings
