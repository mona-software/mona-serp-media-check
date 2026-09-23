# mona-serp-media-check

Công cụ dòng lệnh (CLI) kiểm tra xem một trang web đã sẵn sàng để xuất hiện trên khối **Google Images** và **Google Video** của kết quả tìm kiếm hay chưa.

## Vì sao một trang top Google mà 0 ảnh, 0 video trên SERP là đang bỏ lỡ traffic

Khi khách gõ một từ khóa lên Google, trang kết quả không chỉ có 10 link xanh nữa. Google thường chèn thêm một hàng ảnh ngay giữa trang (khối Google Images) hoặc một khối video ngay đầu trang nếu chủ đề phù hợp. Hai khối này chiếm diện tích màn hình rất lớn, đập vào mắt người dùng trước cả kết quả text thông thường — và với điện thoại, chúng thường nằm ngay phía trên các kết quả text.

Vấn đề là: nếu trang của bạn đang rank tốt bằng nội dung chữ, nhưng ảnh trong bài không có `alt` mô tả, tên file ảnh đặt kiểu `IMG_2031.jpg`, không khai schema `ImageObject`/`VideoObject`, hoặc video nhúng vào bài không có transcript — Google gần như không có đủ dữ liệu để đưa ảnh/video của bạn vào các khối đó. Kết quả là dù bài viết đứng hạng 1 phần kết quả chữ, bạn vẫn nhường toàn bộ diện tích khối ảnh/video hấp dẫn nhất trang cho đối thủ khác — mất một lượng traffic đáng kể mà không hề biết lý do.

`mona-serp-media-check` quét một trang HTML (URL sống hoặc file HTML tải sẵn) và liệt kê chính xác trang đang thiếu tín hiệu nào trong số các tín hiệu Google dùng để quyết định có đưa ảnh/video của trang lên khối kết quả trực quan hay không.

## Công cụ kiểm tra những gì

**Nhóm ảnh** (chỉ xét ảnh trong vùng nội dung chính của bài, bỏ qua logo/icon lặp lại ở header/footer dùng chung cho mọi trang):

- Ảnh nội dung phải có `alt` không rỗng; ảnh trang trí (icon, mũi tên, nền...) được miễn nếu đã đánh dấu `aria-hidden="true"` hoặc `role="presentation"`.
- Chất lượng `alt`: độ dài 6–20 từ, có dấu tiếng Việt nếu trang khai `lang="vi"`, không phải từ vô nghĩa như "image" một mình nếu trang tiếng Anh.
- `alt` không được trùng giữa hai file ảnh khác nhau.
- Tên file ảnh phải có nghĩa (không phải `img001.jpg`), và cần tối thiểu 3 ảnh có tên file chứa từ khóa chính của bài.
- Ảnh không được chỉ có `data-src` (lazy-load) mà thiếu `src` thật.
- Schema `ImageObject` trong JSON-LD: cần tối thiểu 3 khối có `caption`, không được khai ảnh "mồ côi" (ảnh không thật sự có trên trang), nên có đủ `creator`/`creditText`/`copyrightNotice`.
- Mọi khối JSON-LD phải là JSON hợp lệ.
- (Bỏ qua khi chạy `--fast`) Tải thử ảnh chủ lực để đọc kích thước thật, cảnh báo nếu không có ảnh nào đủ lớn để Google ưu tiên; đối chiếu sitemap ảnh (nếu có domain) để tìm ảnh "mồ côi" trong sitemap.

**Nhóm Open Graph image** (ảnh đại diện khi chia sẻ link):

- Có khai `og:image` chưa, tên file có phải ảnh dùng chung/mặc định không, có khai kích thước không, `og:title`/`og:description` có đủ dài không.
- (Bỏ qua khi chạy `--fast`) Ảnh `og:image` tải được, kích thước gần chuẩn 1200×630.

**Nhóm video:**

- Phát hiện video nhúng (YouTube hoặc thẻ `<video>`), kiểm schema `VideoObject` đủ trường (`name`, `description`, `thumbnailUrl`, `uploadDate`, `duration`), có `transcript` đủ dài, có `potentialAction` kiểu `SeekToAction` để lên "khoảnh khắc quan trọng", có đủ chữ bao quanh video, và đối chiếu video-sitemap nếu có.

Công cụ phân biệt hai mức: **lỗi** (chặn hẳn khả năng lên khối ảnh/video, exit code khác 0) và **cảnh báo** (tín hiệu nên có nhưng không bắt buộc).

## Cài đặt

```bash
git clone https://github.com/themonagroup/mona-serp-media-check.git
cd mona-serp-media-check
pip install -e .

# Muốn công cụ đọc kích thước ảnh nhanh hơn qua Pillow (tùy chọn, không bắt buộc):
pip install -e ".[images]"
```

Yêu cầu Python 3.10 trở lên. Phần lõi chỉ dùng thư viện chuẩn của Python, không cần cài thêm gì nếu chỉ chạy chế độ mặc định.

## Cách dùng

```bash
# Kiểm 1 trang đang sống trên mạng
mona-serp-media-check https://example.vn/bai-viet --keyword "thiết kế website"

# Kiểm 1 file HTML tải sẵn, kèm domain gốc để đối chiếu sitemap
mona-serp-media-check ./page.html --keyword "thiết kế website" --base https://example.vn

# --fast: bỏ qua toàn bộ bước tải ảnh/video/sitemap qua mạng, chỉ đọc HTML + JSON-LD tại chỗ
mona-serp-media-check ./page.html --keyword "thiết kế website" --fast

# Xuất JSON để nối vào pipeline khác
mona-serp-media-check ./page.html --keyword "thiết kế website" --fast --json
```

Các tham số:

| Tham số | Bắt buộc | Ý nghĩa |
|---|---|---|
| `target` | Có | URL cần kiểm, hoặc đường dẫn file HTML local |
| `--keyword` | Có | Từ khóa chính của trang |
| `--base` | Không | Domain gốc, dùng khi `target` là file local, để đối chiếu sitemap/resolve link tương đối |
| `--fast` | Không | Bỏ qua các bước tải ảnh/video/sitemap qua mạng |
| `--json` | Không | Xuất kết quả dạng JSON thay vì text |

### Output mẫu thật

File `examples/sample.html` trong repo là một trang mẫu cố tình có vài lỗi (ảnh thiếu `alt`, tên file vô nghĩa, og:image dùng chung, không có video). Chạy:

```bash
mona-serp-media-check examples/sample.html --keyword "thiết kế website" --fast
```

cho ra đúng output sau (chạy thật, dán nguyên văn):

```
Muc tieu kiem tra : (file local)
Tu khoa           : thiết kế website
------------------------------------------------------------

== Nhom ANH ==
  [LOI] [IMG_FILENAME_MEANINGLESS] Ten file anh chua co nghia ro rang: /img001.jpg (tach theo -/_ duoc it hon 3 tu khong phai so).
  [LOI] [IMG_ALT_MISSING] Anh thieu alt text: /img001.jpg
  [CANH BAO] [IMG_ALT_NO_DIACRITICS] Trang khai lang=vi nhung alt cua /anh/thiet-ke-website-ban-hang-mau-1.jpg khong co dau tieng Viet: 'Giao dien trang chu website ban hang mau 1'
  [LOI] [IMG_KEYWORD_FILENAME] Chi co 1 anh co ten file chua tu khoa 'thiết kế website', can toi thieu 3 anh.
  [LOI] [IMAGEOBJECT_CAPTION_COUNT] Chi co 0 khoi ImageObject co 'caption', can toi thieu 3.

== Nhom OPEN GRAPH ==
  [CANH BAO] [OG_IMAGE_GENERIC] Ten file og:image trong giong anh dung chung/mac dinh: https://example.vn/img/default-banner.jpg
  [CANH BAO] [OG_IMAGE_NOT_SPECIFIC] Ten file og:image (https://example.vn/img/default-banner.jpg) khong chua tu khoa hay slug cua trang.
  [CANH BAO] [OG_IMAGE_DIMENSIONS_MISSING] Thieu og:image:width/og:image:height (giup mang xa hoi render nhanh, khong bi giat layout).
  [CANH BAO] [OG_DESCRIPTION_SHORT] og:description qua ngan hoac thieu (can > 20 ky tu).

== Nhom VIDEO ==
  [CANH BAO] [VIDEO_ABSENT] Trang khong co video nao (khong bat buoc, nhung neu chu de phu hop thi video se giup len khoi video cua SERP).
------------------------------------------------------------
Tong ket: 4 loi, 6 canh bao (10 phat hien).
KET QUA: CHUA SAN SANG (con loi can sua)
```

Exit code trả về `0` nếu không có lỗi nào (chỉ còn cảnh báo), và `1` nếu còn ít nhất một lỗi — tiện để gắn vào CI hoặc script kiểm hàng loạt.

## Chạy test

```bash
pip install -e ".[dev]"
pytest
```

Toàn bộ test dùng fixture HTML dựng sẵn và không gọi mạng thật (chế độ `--fast`, hoặc tiêm sẵn một hàm tải giả lập).

---

# mona-serp-media-check (English)

A CLI tool that checks whether a web page is ready to appear in Google's **Images** and **Video** SERP blocks.

## Why a page that ranks well in text but has zero images/video on the SERP is losing traffic

Modern Google results pages are not just ten blue links — Google often inserts an image carousel or a video block right in the middle of (or above) the regular text results, especially on mobile. Those blocks are visually dominant and get clicked heavily.

If your page ranks well in text but its images have no descriptive `alt`, meaningless filenames like `IMG_2031.jpg`, no `ImageObject`/`VideoObject` structured data, or an embedded video with no transcript, Google usually does not have enough signal to surface your media in those blocks — so a competitor's image or video takes that prime real estate instead, even though your text result outranks them.

`mona-serp-media-check` scans a page (live URL or a local HTML file) and reports exactly which of the signals Google relies on for image/video SERP eligibility are missing.

## What it checks

**Images** (scoped to the main content area, excluding shared header/footer/nav chrome):
- Non-decorative images must have non-empty `alt`; decorative images (icon/arrow/bg/logo/decor/spinner/pattern in the filename) are exempt only when marked `aria-hidden="true"` or `role="presentation"`.
- Alt quality: 6–20 words, must contain Vietnamese diacritics when `lang="vi"`, must not be a bare meaningless word like "image" when `lang="en"`.
- Alt text must not be duplicated across two different image files.
- Filenames must be meaningful (not `img001.jpg`), and at least 3 images should have the target keyword in their filename.
- No lazy-loaded-only images (`data-src` without a real `src`).
- `ImageObject` JSON-LD: at least 3 blocks with `caption`, no "orphan" declared images, ideally full `creator`/`creditText`/`copyrightNotice`.
- All JSON-LD blocks must be syntactically valid.
- (Skipped with `--fast`) Downloads a couple of hero images to read real dimensions and flags pages with no sufficiently wide image; cross-checks the image sitemap for orphaned entries.

**Open Graph image:** presence of `og:image`, generic/placeholder filename detection, declared dimensions, `og:title`/`og:description` length, and (non-`--fast`) reachability plus aspect ratio near 1200×630.

**Video:** detects embedded video (YouTube or `<video>`), checks `VideoObject` schema completeness, transcript presence, `SeekToAction` for key moments, surrounding text volume, and (non-`--fast`) the video sitemap.

The tool distinguishes hard **failures** (block SERP media eligibility, non-zero exit code) from soft **warnings** (recommended but not mandatory).

## Install

```bash
git clone https://github.com/themonagroup/mona-serp-media-check.git
cd mona-serp-media-check
pip install -e .
pip install -e ".[images]"   # optional: faster image dimension reading via Pillow
```

Requires Python 3.10+. The core only uses the standard library.

## Usage

```bash
mona-serp-media-check https://example.com/article --keyword "your keyword"
mona-serp-media-check ./page.html --keyword "your keyword" --base https://example.com
mona-serp-media-check ./page.html --keyword "your keyword" --fast
mona-serp-media-check ./page.html --keyword "your keyword" --fast --json
```

See the Vietnamese section above for the full flag table and a real sample run against `examples/sample.html`.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

All tests run against local HTML fixtures and never touch the real network.

## License

MIT — see [LICENSE](LICENSE).

---
Từ MONA — https://mona.media · Các repo khác: https://github.com/themonagroup · Hub mã nguồn mở: https://mona.media/mona-open/
