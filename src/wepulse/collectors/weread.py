from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote

import httpx

from ..models import Account, ArticleCandidate
from .base import Collector, CollectorError


class WeReadCollector(Collector):
    """Low-frequency collector for WeRead's logged-in MP cover endpoint.

    The endpoint is intentionally isolated in one adapter because it is not a
    stable public content API and may change independently of the application.
    """

    def __init__(self, cookie: str, timeout: int, user_agent: str, fetch_content: bool = False):
        self.cookie = cookie
        self.timeout = timeout
        self.user_agent = user_agent
        self.fetch_content = fetch_content

    async def collect(self, account: Account) -> list[ArticleCandidate]:
        if not self.cookie:
            raise CollectorError("未配置 WEREAD_COOKIE")
        if not account.source_id:
            raise CollectorError("微信读书订阅缺少 source_id/bookId")
        headers = {
            "Accept": "application/json, text/plain, */*",
            "Cookie": self.cookie,
            "Referer": "https://weread.qq.com/",
            "User-Agent": self.user_agent,
        }
        url = f"https://weread.qq.com/api/mp/cover?bookId={quote(account.source_id, safe='')}"
        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            payload = response.json()
            self._raise_api_error(payload)
            item = self._find_article(payload)
            if not item:
                raise CollectorError("响应中没有找到最新文章；可能需要重新授权或该公众号暂无内容")
            review_id = str(item.get("reviewId") or item.get("review_id") or "")
            title = str(item.get("title") or item.get("name") or "未命名文章").strip()
            if not review_id:
                raise CollectorError("最新文章缺少 reviewId")
            token = review_id.rsplit("_", 1)[-1].replace("~", "_")
            article_url = str(item.get("url") or item.get("articleUrl") or f"https://mp.weixin.qq.com/s/{token}")
            published = self._published_at(item)
            content = ""
            if self.fetch_content:
                content = await self._content(client, review_id, headers)
        return [ArticleCandidate(
            external_id=review_id,
            title=title,
            url=article_url,
            published_at=published,
            summary=str(item.get("abstract") or item.get("summary") or ""),
            content=content,
            cover_url=str(item.get("cover") or item.get("coverUrl") or ""),
        )]

    async def _content(self, client: httpx.AsyncClient, review_id: str, headers: dict[str, str]) -> str:
        url = f"https://weread.qq.com/web/mp/content?reviewId={quote(review_id, safe='')}"
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        payload = response.json()
        self._raise_api_error(payload)
        return str(payload.get("content") or payload.get("html") or payload.get("data", {}).get("content") or "")

    @staticmethod
    def _raise_api_error(payload: dict[str, Any]) -> None:
        code = payload.get("errCode", payload.get("errcode", payload.get("code", 0)))
        if code not in (0, "0", None):
            message = payload.get("errMsg") or payload.get("errmsg") or payload.get("message") or "未知错误"
            raise CollectorError(f"微信读书接口错误 {code}：{message}")

    @classmethod
    def _find_article(cls, value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            if ("reviewId" in value or "review_id" in value) and ("title" in value or "name" in value):
                return value
            for child in value.values():
                found = cls._find_article(child)
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = cls._find_article(child)
                if found:
                    return found
        return None

    @staticmethod
    def _published_at(item: dict[str, Any]) -> datetime:
        raw = item.get("publishTime") or item.get("createTime") or item.get("timestamp")
        try:
            number = float(raw)
            if number > 10_000_000_000:
                number /= 1000
            return datetime.fromtimestamp(number, timezone.utc)
        except (TypeError, ValueError, OSError):
            return datetime.now(timezone.utc)
