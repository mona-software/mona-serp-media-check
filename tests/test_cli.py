import json

from mona_serp_media_check.cli import main

from tests.helpers import wrap_html


def test_cli_exits_nonzero_when_fail_present(tmp_path, capsys):
    html = wrap_html("<main><img src='/img001.jpg'></main>")
    fixture = tmp_path / "page.html"
    fixture.write_text(html, encoding="utf-8")

    exit_code = main([str(fixture), "--keyword", "thiết kế website", "--fast", "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)

    assert exit_code == 1
    assert data["summary"]["fail"] > 0


def test_cli_json_output_is_valid_and_has_target(tmp_path, capsys):
    head = (
        '<meta property="og:image" content="https://example.vn/anh/thiet-ke-website-og.jpg">'
        '<meta property="og:image:width" content="1200">'
        '<meta property="og:image:height" content="630">'
        '<meta property="og:title" content="Thiết kế website chuẩn SEO">'
        '<meta property="og:description" content="Bài viết hướng dẫn thiết kế website chuẩn SEO chi tiết cho người mới">'
    )
    body = (
        '<main>'
        '<img src="/anh/thiet-ke-website-a.jpg" alt="Giao diện website mẫu chuẩn SEO cho doanh nghiệp">'
        '<img src="/anh/thiet-ke-website-b.jpg" alt="Trang chủ website mẫu chuẩn SEO cho cửa hàng nhỏ">'
        '<img src="/anh/thiet-ke-website-c.jpg" alt="Giao diện quản trị website mẫu dành cho quản lý bán hàng">'
        "</main>"
    )
    html = wrap_html(body, head_extra=head)
    fixture = tmp_path / "page.html"
    fixture.write_text(html, encoding="utf-8")

    main([str(fixture), "--keyword", "thiết kế website", "--fast", "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["target"] == "(file local)"
    assert data["keyword"] == "thiết kế website"


def test_cli_text_output_mentions_result(tmp_path, capsys):
    html = wrap_html("<main><p>trang khong co gi</p></main>")
    fixture = tmp_path / "page.html"
    fixture.write_text(html, encoding="utf-8")

    main([str(fixture), "--keyword", "thiết kế website", "--fast"])
    out = capsys.readouterr().out
    assert "KET QUA" in out
