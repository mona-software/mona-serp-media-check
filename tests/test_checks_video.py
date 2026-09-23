from mona_serp_media_check import checks_video
from mona_serp_media_check.htmlparse import parse_html

from tests.helpers import BASE_URL, wrap_html


def codes(findings):
    return {f.code for f in findings}


def test_no_video_only_soft_warning():
    html = wrap_html("<main><p>" + ("noi dung " * 50) + "</p></main>")
    page = parse_html(html)
    findings = checks_video.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert codes(findings) == {"VIDEO_ABSENT"}


def test_video_without_schema_warns():
    body = '<main><video src="/video/gioi-thieu.mp4"></video><p>' + ("noi dung " * 320) + "</p></main>"
    html = wrap_html(body)
    page = parse_html(html)
    findings = checks_video.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "VIDEOOBJECT_MISSING" in codes(findings)


def test_video_with_full_schema_has_no_field_warning():
    ld_json = (
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"VideoObject",'
        '"name":"Video huong dan thiet ke website chuan SEO",'
        '"description":"Video huong dan chi tiet tung buoc thiet ke website chuan SEO cho nguoi moi",'
        '"thumbnailUrl":"https://example.vn/video/thumb.jpg",'
        '"uploadDate":"2026-01-01",'
        '"duration":"PT5M30S",'
        '"transcript":"' + ("Day la transcript day du cua video. " * 10) + '",'
        '"potentialAction":{"@type":"SeekToAction","target":"https://example.vn/video#t={seek_to_second_number}","startOffset-input":"required name=seek_to_second_number"}}'
        "</script>"
    )
    body = (
        '<main><video src="/video/gioi-thieu.mp4"></video><p>'
        + ("noi dung " * 320)
        + "</p></main>"
    )
    html = wrap_html(body, head_extra=ld_json)
    page = parse_html(html)
    findings = checks_video.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "VIDEOOBJECT_FIELDS_MISSING" not in codes(findings)
    assert "VIDEO_TRANSCRIPT_MISSING" not in codes(findings)
    assert "VIDEO_NO_SEEK_ACTION" not in codes(findings)
    assert "VIDEO_CONTEXT_TEXT_THIN" not in codes(findings)


def test_video_missing_transcript_warns():
    ld_json = (
        '<script type="application/ld+json">'
        '{"@context":"https://schema.org","@type":"VideoObject",'
        '"name":"Video huong dan thiet ke website",'
        '"description":"Mo ta ngan",'
        '"thumbnailUrl":"https://example.vn/video/thumb.jpg",'
        '"uploadDate":"2026-01-01",'
        '"duration":"PT5M30S"}'
        "</script>"
    )
    body = '<main><video src="/video/gioi-thieu.mp4"></video></main>'
    html = wrap_html(body, head_extra=ld_json)
    page = parse_html(html)
    findings = checks_video.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "VIDEO_TRANSCRIPT_MISSING" in codes(findings)


def test_thin_surrounding_text_warns():
    body = '<main><video src="/video/gioi-thieu.mp4"></video><p>chi vai chu thoi</p></main>'
    html = wrap_html(body)
    page = parse_html(html)
    findings = checks_video.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "VIDEO_CONTEXT_TEXT_THIN" in codes(findings)


def test_youtube_link_detected_as_video():
    body = '<main><a href="https://youtu.be/abc123">Xem video</a></main>'
    html = wrap_html(body)
    page = parse_html(html)
    findings = checks_video.run(page, "thiết kế website", base_url=BASE_URL, fast=True)
    assert "VIDEO_ABSENT" not in codes(findings)
