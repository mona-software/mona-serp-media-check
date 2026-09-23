"""Giao dien dong lenh cho mona-serp-media-check."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import checks_image, checks_og, checks_video
from . import fetch as fetch_mod
from .htmlparse import parse_html
from .models import Report

SEVERITY_ICON = {"fail": "[LOI]", "warn": "[CANH BAO]", "pass": "[OK]"}


def _looks_like_url(target: str) -> bool:
    return target.startswith("http://") or target.startswith("https://")


def _load_html(target: str) -> tuple[str, str]:
    """Tra ve (html, page_url_de_resolve_link).

    Voi URL: page_url chinh la URL do. Voi file local: page_url la
    chuoi rong tru khi nguoi dung truyen --base, luc do se ghep sau.
    """
    if _looks_like_url(target):
        html = fetch_mod.fetch_text(target)
        if html is None:
            raise SystemExit(f"Khong tai duoc noi dung tu {target}")
        return html, target

    path = Path(target)
    if not path.exists():
        raise SystemExit(f"Khong tim thay file: {target}")
    return path.read_text(encoding="utf-8", errors="replace"), ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mona-serp-media-check",
        description=(
            "Kiem tra 1 trang web da san sang len khoi Google Images / "
            "Google Video tren SERP hay chua."
        ),
    )
    parser.add_argument("target", help="URL can kiem tra, hoac duong dan file HTML local")
    parser.add_argument("--keyword", required=True, help="Tu khoa chinh cua trang (bat buoc)")
    parser.add_argument(
        "--base",
        default="",
        help="Domain goc (vd: https://example.com) -- dung khi target la file HTML local, "
        "de doi chieu sitemap va resolve link tuong doi",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Bo qua cac buoc tai anh/video/sitemap qua mang, chi kiem tra tren HTML+JSON-LD",
    )
    parser.add_argument("--json", action="store_true", help="Xuat ket qua dang JSON")
    return parser


def run_all_checks(html: str, keyword: str, page_url: str, base: str, fast: bool, fetcher=None) -> Report:
    page = parse_html(html)
    base_url = base or page_url
    report = Report(url_or_path=page_url or "(file local)", keyword=keyword)

    report.extend(
        checks_image.run(page, keyword, base_url=base_url, fast=fast, fetcher=fetcher)
    )
    report.extend(
        checks_og.run(
            page, keyword, page_url=page_url, base_url=base_url, fast=fast, fetcher=fetcher
        )
    )
    report.extend(
        checks_video.run(page, keyword, base_url=base_url, fast=fast, fetcher=fetcher)
    )
    return report


def format_text_report(report: Report) -> str:
    lines = []
    lines.append(f"Muc tieu kiem tra : {report.url_or_path}")
    lines.append(f"Tu khoa           : {report.keyword}")
    lines.append("-" * 60)

    if not report.findings:
        lines.append("Khong co phat hien nao.")
    else:
        by_group: dict[str, list] = {}
        for finding in report.findings:
            by_group.setdefault(finding.group, []).append(finding)

        group_labels = {"image": "ANH", "og": "OPEN GRAPH", "video": "VIDEO"}
        for group, items in by_group.items():
            lines.append(f"\n== Nhom {group_labels.get(group, group.upper())} ==")
            for f in items:
                icon = SEVERITY_ICON.get(f.severity, f.severity.upper())
                lines.append(f"  {icon} [{f.code}] {f.message}")

    lines.append("-" * 60)
    lines.append(
        f"Tong ket: {report.fail_count} loi, {report.warn_count} canh bao "
        f"({len(report.findings)} phat hien)."
    )
    lines.append("KET QUA: SAN SANG" if report.is_ok else "KET QUA: CHUA SAN SANG (con loi can sua)")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    html, page_url = _load_html(args.target)
    report = run_all_checks(
        html=html,
        keyword=args.keyword,
        page_url=page_url,
        base=args.base,
        fast=args.fast,
    )

    if args.json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(format_text_report(report))

    return 0 if report.is_ok else 1


if __name__ == "__main__":
    sys.exit(main())
