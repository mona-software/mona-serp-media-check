"""Doc kich thuoc that (width, height) cua anh tu bytes.

Pillow la dependency TUY CHON. Neu co Pillow thi dung cho nhanh va day
du dinh dang; neu khong co, roi ve cac ham tu viet doc header nhi phan
cua 4 dinh dang pho bien nhat tren web: PNG, JPEG, GIF, WEBP. Cach nay
giup cong cu chay duoc tren moi may ma khong bat buoc cai them thu vien.
"""

from __future__ import annotations

import struct

try:  # pragma: no cover - phu thuoc vao moi truong co Pillow hay khong
    from PIL import Image  # type: ignore

    _HAS_PIL = True
except Exception:  # pragma: no cover
    _HAS_PIL = False


def get_image_dimensions(data: bytes) -> tuple[int, int] | None:
    """Tra ve (width, height) hoac None neu khong doc duoc."""
    if not data:
        return None

    if _HAS_PIL:
        try:  # pragma: no cover - chi chay khi co Pillow
            import io

            with Image.open(io.BytesIO(data)) as img:
                return img.width, img.height
        except Exception:
            pass  # roi xuong cac parser tu viet ben duoi

    for parser in (_read_png, _read_gif, _read_jpeg, _read_webp):
        try:
            dims = parser(data)
        except Exception:
            dims = None
        if dims:
            return dims
    return None


def _read_png(data: bytes) -> tuple[int, int] | None:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if data[12:16] != b"IHDR":
        return None
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def _read_gif(data: bytes) -> tuple[int, int] | None:
    if data[:6] not in (b"GIF87a", b"GIF89a"):
        return None
    width, height = struct.unpack("<HH", data[6:10])
    return width, height


def _read_jpeg(data: bytes) -> tuple[int, int] | None:
    if data[:2] != b"\xff\xd8":
        return None
    idx = 2
    size = len(data)
    while idx < size:
        if data[idx] != 0xFF:
            idx += 1
            continue
        marker = data[idx + 1]
        # SOFx markers chua kich thuoc, tru cac marker DHT/JPG-ext dac biet
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            block_len = struct.unpack(">H", data[idx + 2: idx + 4])[0]
            height, width = struct.unpack(">HH", data[idx + 5: idx + 9])
            return width, height
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            idx += 2
            continue
        if idx + 4 > size:
            break
        block_len = struct.unpack(">H", data[idx + 2: idx + 4])[0]
        idx += 2 + block_len
    return None


def _read_webp(data: bytes) -> tuple[int, int] | None:
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk_id = data[12:16]
    if chunk_id == b"VP8X":
        b0, b1, b2 = data[24], data[25], data[26]
        width = (b0 | (b1 << 8) | ((b2 & 0x00) << 16)) + 1
        # width/height la so 24-bit (little-endian, tru 1)
        width = (data[24] | (data[25] << 8) | (data[26] << 16)) + 1
        height = (data[27] | (data[28] << 8) | (data[29] << 16)) + 1
        return width, height
    if chunk_id == b"VP8 ":
        # bitstream VP8: tim ma "start code" 0x9d 0x01 0x2a roi 2 byte
        # width + 2 byte height (14 bit thap, che 2 bit cao la scale)
        sync_idx = data.find(b"\x9d\x01\x2a", 20, 40)
        if sync_idx == -1:
            return None
        w_bytes = data[sync_idx + 3: sync_idx + 5]
        h_bytes = data[sync_idx + 5: sync_idx + 7]
        width = struct.unpack("<H", w_bytes)[0] & 0x3FFF
        height = struct.unpack("<H", h_bytes)[0] & 0x3FFF
        return width, height
    if chunk_id == b"VP8L":
        chunk = data[20:25]
        if len(chunk) < 5 or chunk[0] != 0x2F:
            return None
        bits = int.from_bytes(chunk[1:5], "little")
        width = (bits & 0x3FFF) + 1
        height = ((bits >> 14) & 0x3FFF) + 1
        return width, height
    return None
