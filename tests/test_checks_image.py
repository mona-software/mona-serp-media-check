from mona_serp_media_check import checks_image
from mona_serp_media_check.htmlparse import parse_html

from tests.helpers import BASE_URL, PNG_1X1, make_fake_fetcher, failing_fetcher, wrap_html


def codes(findings):
    return {f.code for f in findings}


def test_missing_alt_fails():
    html = wrap_html(
        '<main><img src="/anh/ban-hang-online-tang-doanh-thu.jpg"></main>'
    )
    page = parse_html(html)
    findings = checks_image.run(page, "ban hang online", base_url=BASE_URL, fast=True)
    assert "IMG_ALT_MISSING" in codes(findings)


def test_good_content_image_has_no_alt_missing():
    html = wrap_html(
        '<main><img src="/anh/thiet-ke-website-ban-hang-2026.jpg" '
        'alt="Giao diện website bán hàng chuẩn SEO cho doanh nghiệp nhỏ"></main>'
    )
    page = parse_html(html)
    findings = checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "IMG_ALT_MISSING" not in codes(findings)
    assert "IMG_ALT_NO_DIACRITICS" not in codes(findings)


def test_decorative_image_with_aria_hidden_is_exempt():
    html = wrap_html(
        '<main><img src="/icon-arrow-right.png" aria-hidden="true"></main>'
    )
    page = parse_html(html)
    findings = checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "IMG_ALT_MISSING" not in codes(findings)
    assert "IMG_FILENAME_MEANINGLESS" not in codes(findings)


def test_meaningless_filename_fails():
    html = wrap_html('<main><img src="/img001.jpg" alt="Một bức ảnh minh họa đẹp mắt"></main>')
    page = parse_html(html)
    findings = checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "IMG_FILENAME_MEANINGLESS" in codes(findings)


def test_duplicate_alt_different_files_fails():
    html = wrap_html(
        """
        <main>
        <img src="/anh/thiet-ke-web-chuan-seo-a.jpg" alt="Ảnh minh họa website chuẩn SEO cho khách hàng">
        <img src="/anh/thiet-ke-web-chuan-seo-b.jpg" alt="Ảnh minh họa website chuẩn SEO cho khách hàng">
        </main>
        """
    )
    page = parse_html(html)
    findings = checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "IMG_ALT_DUPLICATE" in codes(findings)


def test_same_file_repeated_alt_is_not_duplicate_error():
    html = wrap_html(
        """
        <main>
        <img src="/anh/thiet-ke-web-chuan-seo.jpg" alt="Ảnh minh họa website chuẩn SEO cho khách hàng">
        <img src="/anh/thiet-ke-web-chuan-seo.jpg" alt="Ảnh minh họa website chuẩn SEO cho khách hàng">
        </main>
        """
    )
    page = parse_html(html)
    findings = checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "IMG_ALT_DUPLICATE" not in codes(findings)


def test_keyword_filename_count_fails_when_below_threshold():
    html = wrap_html(
        '<main><img src="/anh/mot-tam-hinh-bat-ky.jpg" alt="Một tấm hình minh họa bất kỳ nào đó"></main>'
    )
    page = parse_html(html)
    findings = checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "IMG_KEYWORD_FILENAME" in codes(findings)


def test_lazy_only_image_fails():
    html = wrap_html('<main><img data-src="/anh/thiet-ke-website-lazyload.jpg"></main>')
    page = parse_html(html)
    findings = checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "IMG_LAZY_ONLY" in codes(findings)


def test_jsonld_syntax_error_fails():
    html = wrap_html(
        '<main><img src="/anh/thiet-ke-website-a.jpg" alt="Website chuẩn SEO cho công ty vừa và nhỏ"></main>',
        head_extra='<script type="application/ld+json">{ khong hop le json, }</script>',
    )
    page = parse_html(html)
    findings = checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "JSONLD_PARSE_ERROR" in codes(findings)


def test_imageobject_orphan_fails():
    ld_json = (
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"ImageObject",'
        '"contentUrl":"https://example.vn/khong-co-tren-trang.jpg",'
        '"caption":"Ảnh không tồn tại trên trang"}'
        "</script>"
    )
    html = wrap_html(
        '<main><img src="/anh/thiet-ke-website-a.jpg" alt="Website chuẩn SEO cho công ty vừa và nhỏ"></main>',
        head_extra=ld_json,
    )
    page = parse_html(html)
    findings = checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "IMAGEOBJECT_ORPHAN" in codes(findings)


def test_imageobject_caption_count_fails_when_below_three():
    ld_json = (
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"ImageObject",'
        f'"contentUrl":"{BASE_URL}/anh/thiet-ke-website-a.jpg",'
        '"caption":"Ảnh website chuẩn SEO"}'
        "</script>"
    )
    html = wrap_html(
        '<main><img src="/anh/thiet-ke-website-a.jpg" alt="Website chuẩn SEO cho công ty vừa và nhỏ"></main>',
        head_extra=ld_json,
    )
    page = parse_html(html)
    findings = checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "IMAGEOBJECT_CAPTION_COUNT" in codes(findings)


def test_fast_mode_never_touches_network():
    html = wrap_html(
        '<main><img src="/anh/thiet-ke-website-a.jpg" alt="Website chuẩn SEO cho công ty vừa và nhỏ"></main>'
    )
    page = parse_html(html)
    # fetcher gia se raise neu bi goi -- --fast phai tranh hoan toan
    checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=True, fetcher=failing_fetcher)


def test_non_fast_mode_flags_small_images():
    html = wrap_html(
        '<main><img src="/anh/thiet-ke-website-nho.jpg" alt="Website chuẩn SEO cho công ty vừa và nhỏ"></main>'
    )
    page = parse_html(html)
    fetcher = make_fake_fetcher({"https://example.vn/anh/thiet-ke-website-nho.jpg": PNG_1X1})
    findings = checks_image.run(page, "thiết kế website", base_url=BASE_URL, fast=False, fetcher=fetcher)
    assert "IMG_TOO_SMALL" in codes(findings)
