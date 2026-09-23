from mona_serp_media_check import checks_og
from mona_serp_media_check.htmlparse import parse_html

from tests.helpers import BASE_URL, wrap_html


def codes(findings):
    return {f.code for f in findings}


def test_missing_og_image_fails():
    html = wrap_html("<main><p>Khong co the og:image</p></main>")
    page = parse_html(html)
    findings = checks_og.run(page, "thiết kế website", page_url=BASE_URL, fast=True)
    assert "OG_IMAGE_MISSING" in codes(findings)


def test_valid_og_has_no_findings():
    head = (
        '<meta property="og:image" content="https://example.vn/anh/thiet-ke-website-og.jpg">'
        '<meta property="og:image:width" content="1200">'
        '<meta property="og:image:height" content="630">'
        '<meta property="og:title" content="Thiết kế website chuẩn SEO cho doanh nghiệp">'
        '<meta property="og:description" content="Bài viết hướng dẫn thiết kế website chuẩn SEO chi tiết từng bước cho người mới bắt đầu">'
    )
    html = wrap_html("<main><p>noi dung</p></main>", head_extra=head)
    page = parse_html(html)
    findings = checks_og.run(page, "thiết kế website", page_url=BASE_URL, fast=True)
    assert findings == []


def test_generic_og_filename_warns():
    head = '<meta property="og:image" content="https://example.vn/img/default-banner.jpg">'
    html = wrap_html("<main><p>noi dung</p></main>", head_extra=head)
    page = parse_html(html)
    findings = checks_og.run(page, "thiết kế website", page_url=BASE_URL, fast=True)
    assert "OG_IMAGE_GENERIC" in codes(findings)


def test_og_missing_dimensions_warns():
    head = '<meta property="og:image" content="https://example.vn/anh/thiet-ke-website-og.jpg">'
    html = wrap_html("<main><p>noi dung</p></main>", head_extra=head)
    page = parse_html(html)
    findings = checks_og.run(page, "thiết kế website", page_url=BASE_URL, fast=True)
    assert "OG_IMAGE_DIMENSIONS_MISSING" in codes(findings)
