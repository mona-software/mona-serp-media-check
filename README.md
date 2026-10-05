# mona-serp-media-check

A command-line tool that checks whether a web page has the image, video and Open Graph signals Google uses to show its media in Google Images and video results.

[![test](https://github.com/mona-software/mona-serp-media-check/actions/workflows/test.yml/badge.svg)](https://github.com/mona-software/mona-serp-media-check/actions/workflows/test.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

It scans a live URL or a local HTML file and lists missing or weak signals: alt text, image filenames, `ImageObject`/`VideoObject` structured data, video transcripts, image/video sitemaps and `og:image`. Findings are either failures (exit code 1) or warnings. Console messages are in Vietnamese without diacritics; some checks (such as diacritics in alt text when the page declares `lang="vi"`) are aimed at Vietnamese pages.

## Install

Requires Python 3.10+. The core uses only the standard library.

```bash
git clone https://github.com/mona-software/mona-serp-media-check
cd mona-serp-media-check
pip install -e .
# Optional: read image dimensions with Pillow
pip install -e ".[images]"
```

## Usage

```bash
# Check a live page
mona-serp-media-check https://example.vn/article --keyword "thiết kế website"

# Check a local HTML file, with the site root for sitemap lookups and relative links
mona-serp-media-check ./page.html --keyword "thiết kế website" --base https://example.vn

# --fast: skip all network requests for images, video and sitemaps; check HTML and JSON-LD only
mona-serp-media-check ./page.html --keyword "thiết kế website" --fast

# JSON output
mona-serp-media-check ./page.html --keyword "thiết kế website" --fast --json
```

| Option | Required | Description |
| --- | --- | --- |
| `target` | yes | URL or path to a local HTML file |
| `--keyword` | yes | The page's primary keyword |
| `--base` | no | Site root (e.g. `https://example.com`) when `target` is a local file |
| `--fast` | no | Skip network requests for images, video and sitemaps |
| `--json` | no | Print JSON instead of text |

Exit codes: `0` when there are no failures (warnings allowed), `1` when at least one failure is found.

### Example

`examples/sample.html` is a sample page with deliberate problems:

```bash
mona-serp-media-check examples/sample.html --keyword "thiết kế website" --fast
```

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

`[LOI]` is a failure and `[CANH BAO]` is a warning.

With `--json`, the output contains `target`, `keyword`, `summary` (`fail`, `warn`, `pass` counts) and `findings` (each with `severity`, `group`, `code`, `message`).

## Checks

**Images** (main content only; repeated header/footer/nav images are ignored):

- Content images need a non-empty `alt`. Decorative images are exempt when marked `aria-hidden="true"` or `role="presentation"`.
- Alt text is 6–20 words, contains Vietnamese diacritics when the page declares `lang="vi"`, and is not a bare placeholder word such as "image" on `lang="en"` pages.
- The same alt text is not reused for different image files.
- Filenames are descriptive (not `img001.jpg`), and at least 3 filenames contain the keyword.
- Images do not rely on `data-src` alone without a real `src`.
- `ImageObject` JSON-LD: at least 3 blocks with `caption`, no declared images missing from the page, and `creator`/`creditText`/`copyrightNotice` present.
- Every JSON-LD block parses as valid JSON.
- Without `--fast`: downloads main images to read their size (warns if none is at least 1200 px wide) and compares the image sitemap with the page.

**Open Graph:** `og:image` present, generic or default filename, filename unrelated to the keyword or slug, declared `og:image:width`/`og:image:height`, `og:title` present, `og:description` longer than 20 characters. Without `--fast`: the image is reachable and its ratio is close to 1200×630.

**Video:** detects YouTube embeds and `<video>` tags, then checks `VideoObject` fields (`name`, `description`, `thumbnailUrl`, `uploadDate`, `duration`), a `transcript` longer than 200 characters, a `SeekToAction` in `potentialAction`, at least 300 words of page text, and, without `--fast`, thumbnail reachability and the video sitemap.

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests use local HTML fixtures and a stub fetcher; they make no network requests.

## License

MIT, see [LICENSE](LICENSE).

**`mona-serp-media-check` is a product of MONA Software, a member of The MONA Group.**
