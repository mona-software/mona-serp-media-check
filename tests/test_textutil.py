from mona_serp_media_check.textutil import (
    filename_matches_keyword,
    filename_meaningful_words,
    filename_stem,
    has_vietnamese_diacritics,
    strip_diacritics,
    word_count,
)


def test_strip_diacritics_basic():
    assert strip_diacritics("Thiết kế website") == "Thiet ke website"


def test_has_vietnamese_diacritics_true_false():
    assert has_vietnamese_diacritics("Máy chủ Đà Nẵng") is True
    assert has_vietnamese_diacritics("May chu Da Nang") is False


def test_filename_stem_and_meaningful_words():
    stem = filename_stem("https://x.vn/anh/thiet-ke-website-chuan-seo-2026.jpg?v=2")
    assert stem == "thiet-ke-website-chuan-seo-2026"
    words = filename_meaningful_words(stem)
    assert "2026" not in words
    assert len(words) >= 3


def test_filename_matches_keyword():
    assert filename_matches_keyword("thiet-ke-website-chuan-seo", "thiết kế website") is True
    assert filename_matches_keyword("img001", "thiết kế website") is False


def test_word_count():
    assert word_count("mot hai ba") == 3
    assert word_count("   ") == 0
