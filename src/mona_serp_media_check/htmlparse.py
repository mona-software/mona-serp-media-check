"""Parser HTML nhe, chi dung thu vien chuan (html.parser).

Muc tieu khong phai dung mot DOM day du, ma chi rut trich vua du du lieu
de cac module checks_* lam viec: the <img>, the <meta>, khoi JSON-LD,
video/iframe nhung va tong so chu cua trang. Vi khong dung DOM cay day
du, ta theo doi "ngan xep the dang mo" de biet mot phan tu co nam trong
vung noi dung chinh (main/article) hay vung khung chung (header/footer/
nav/aside) hay khong -- day la tin hieu quan trong de khong bat loi oan
cho logo/icon lap lai o moi trang.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser

# Cac the duoc xem la "khung chung" cua site (lap lai moi trang), nen
# loai tru khoi vung noi dung chinh khi xet chat luong alt/anh.
CHROME_TAGS = {"header", "footer", "nav"}
MAIN_TAGS = {"main", "article"}

VOID_TAGS = {
    "img", "meta", "link", "br", "hr", "input", "source", "track",
    "area", "base", "col", "embed", "param", "wbr",
}


@dataclass
class ImgTag:
    attrs: dict
    ancestors: list
    in_main: bool
    in_chrome: bool


@dataclass
class VideoTag:
    kind: str  # "html5" | "youtube_embed"
    attrs: dict
    ancestors: list
    in_main: bool
    sources: list = field(default_factory=list)


@dataclass
class PageIndex:
    lang: str = ""
    has_main_region: bool = False
    imgs: list = field(default_factory=list)
    metas: list = field(default_factory=list)
    ld_json_blocks: list = field(default_factory=list)
    videos: list = field(default_factory=list)
    total_word_count: int = 0
    title_text: str = ""


class _Indexer(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.page = PageIndex()
        self._in_script_ldjson = False
        self._ldjson_buffer: list[str] = []
        self._in_title = False
        self._word_chunks: list[str] = []
        self._current_video: VideoTag | None = None

    # -- tien ich noi bo --------------------------------------------
    def _in_main(self) -> bool:
        return any(tag in MAIN_TAGS for tag in self.stack)

    def _in_chrome(self) -> bool:
        return any(tag in CHROME_TAGS for tag in self.stack)

    def _handle_open(self, tag: str, attrs_list) -> None:
        attrs = {k: (v if v is not None else "") for k, v in attrs_list}

        if tag == "html":
            self.page.lang = attrs.get("lang", "").strip()

        if tag in MAIN_TAGS:
            self.page.has_main_region = True

        if tag == "title":
            self._in_title = True

        if tag == "script" and attrs.get("type", "").lower() == "application/ld+json":
            self._in_script_ldjson = True
            self._ldjson_buffer = []

        if tag == "meta":
            self.page.metas.append(attrs)

        if tag == "img":
            self.page.imgs.append(
                ImgTag(
                    attrs=attrs,
                    ancestors=list(self.stack),
                    in_main=self._in_main(),
                    in_chrome=self._in_chrome(),
                )
            )

        if tag == "video":
            self._current_video = VideoTag(
                kind="html5",
                attrs=attrs,
                ancestors=list(self.stack),
                in_main=self._in_main(),
                sources=[],
            )
            self.page.videos.append(self._current_video)

        if tag == "source" and self._current_video is not None and "video" in self.stack:
            self._current_video.sources.append(attrs)

        if tag == "iframe":
            src = attrs.get("src", "")
            if "youtube.com" in src or "youtu.be" in src:
                self.page.videos.append(
                    VideoTag(
                        kind="youtube_embed",
                        attrs=attrs,
                        ancestors=list(self.stack),
                        in_main=self._in_main(),
                        sources=[],
                    )
                )

        if tag == "a":
            href = attrs.get("href", "")
            if "youtube.com/watch" in href or "youtu.be/" in href:
                self.page.videos.append(
                    VideoTag(
                        kind="youtube_embed",
                        attrs=attrs,
                        ancestors=list(self.stack),
                        in_main=self._in_main(),
                        sources=[],
                    )
                )

    def handle_starttag(self, tag, attrs_list):
        self._handle_open(tag, attrs_list)
        if tag not in VOID_TAGS:
            self.stack.append(tag)
        if tag == "video":
            # video khong phai void nhung ta da push rieng qua stack o tren
            pass

    def handle_startendtag(self, tag, attrs_list):
        self._handle_open(tag, attrs_list)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._in_script_ldjson:
            self._in_script_ldjson = False
            raw = "".join(self._ldjson_buffer).strip()
            if raw:
                self.page.ld_json_blocks.append(raw)
            self._ldjson_buffer = []
        if tag == "video":
            self._current_video = None
        while self.stack and tag in self.stack:
            popped = self.stack.pop()
            if popped == tag:
                break

    def handle_data(self, data):
        if self._in_script_ldjson:
            self._ldjson_buffer.append(data)
            return
        if self._in_title:
            self.page.title_text += data
        if self.stack and self.stack[-1] in ("script", "style"):
            return
        text = data.strip()
        if text:
            self._word_chunks.append(text)

    def close(self):
        super().close()
        self.page.total_word_count = sum(
            len(chunk.split()) for chunk in self._word_chunks
        )


def parse_html(html: str) -> PageIndex:
    parser = _Indexer()
    parser.feed(html)
    parser.close()
    return parser.page
