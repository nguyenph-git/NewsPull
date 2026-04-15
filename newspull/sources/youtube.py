import httpx
import xml.etree.ElementTree as ET

from .base import Source
from ..models import RawArticle

YT_RSS = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "media": "http://search.yahoo.com/mrss/",
}


class YouTubeSource(Source):
    def __init__(self, channel_id: str):
        self._channel_id = channel_id

    @property
    def name(self) -> str:
        return f"youtube:{self._channel_id}"

    def fetch(self) -> list[RawArticle]:
        url = YT_RSS.format(channel_id=self._channel_id)
        try:
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            root = ET.fromstring(response.text)
            articles = []
            for entry in root.findall("atom:entry", NS):
                title_el = entry.find("atom:title", NS)
                link_el = entry.find("atom:link", NS)
                desc_el = entry.find("media:group/media:description", NS)

                title = title_el.text if title_el is not None else "Untitled"
                video_url = link_el.get("href", "") if link_el is not None else ""
                content = desc_el.text if desc_el is not None else ""

                if not video_url:
                    continue
                articles.append(
                    RawArticle(
                        title=title,
                        url=video_url,
                        source="youtube",
                        content=(content or "")[:4000],
                    )
                )
            return articles
        except Exception:
            return []
