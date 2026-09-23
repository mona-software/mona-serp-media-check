from mona_serp_media_check.image_dims import get_image_dimensions
from tests.helpers import make_png


def test_png_dimensions_roundtrip():
    data = make_png(37, 51)
    assert get_image_dimensions(data) == (37, 51)


def test_unknown_bytes_returns_none():
    assert get_image_dimensions(b"khong-phai-anh") is None


def test_empty_bytes_returns_none():
    assert get_image_dimensions(b"") is None
