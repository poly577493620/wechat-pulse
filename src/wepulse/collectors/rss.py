import hashlib
from datetime import datetime, timezone

import feedparser
import httpx
from dateutil import parser as date_parser

from ..models import Account, ArticleCandidate
from .base import Collector, CollectorError


class RssCollector(Collector):
    def __init__(self, timeout: int, user_agent: str):
        self.timeout = timeout
        self.user_agent = user_agent

    async def collect(self, account: Account) -> list[ArticleCandidate]:
        if not account.feed_url:
            raise CollectorError("RSS 订阅缺少 feed_url")
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(account.feed_url, headers={"User-Agent": self.user_agent})
            response.raise_for_status()
        feed = feedparser.parse(response.content)
        if feed.bozo and not feed.entries:
            raise CollectorError(f"RSS 解析失败：{feed.bozo_exception}")
        articles: list[ArticleCandidate] = []
        for entry in feed.entries:
            url = entry.get("link", "").strip()
            title = entry.get("title", "未命名文章").strip()
            external_id = entry.get("id") or entry.get("guid") or url
            if not external_id:
                external_id = hashlib.sha256(f"{title}|{entry}".encode()).hexdigest()
            date_text = entry.get("published") or entry.get("updated")
            try:
                published = date_parser.parse(date_text).astimezone(timezone.utc) if date_text else datetime.now(timezone.utc)
            except (ValueError, TypeError):
                published = datetime.now(timezone.utc)
            articles.append(ArticleCandidate(
                external_id=str(external_id), title=title, url=url,
                published_at=published, summary=entry.get("summary", ""),
            ))
        return articles
