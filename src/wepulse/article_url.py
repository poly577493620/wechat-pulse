import base64
import html
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx

from .models import ArticleCandidate


class ArticleUrlError(ValueError):
    pass


@dataclass(slots=True)
class ResolvedArticle:
    account_name: str
    source_id: str
    article: ArticleCandidate


def _match(page: str, patterns: list[str]) -> str:
    for pattern in patterns:
        match = re.search(pattern, page, flags=re.DOTALL)
        if match:
            value = html.unescape(match.group(1)).strip()
            try:
                return json.loads(f'"{value}"')
            except (json.JSONDecodeError, UnicodeDecodeError):
                return value
    return ""


def parse_article_page(url: str, page: str) -> ResolvedArticle:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "mp.weixin.qq.com":
        raise ArticleUrlError("只接受 https://mp.weixin.qq.com/ 的公开文章链接")

    title = _match(page, [r'<meta\s+property="og:title"\s+content="([^"]*)"'])
    account_name = _match(page, [
        r'var\s+nickname\s*=\s*htmlDecode\("(.*?)"\)',
        r'var\s+nickname\s*=\s*"(.*?)"',
    ])
    biz = _match(page, [r'biz\s*:\s*"([^"]+)"', r'var\s+biz\s*=\s*"([^"]+)"'])
    mid = _match(page, [r'mid\s*:\s*"([^"]+)"', r'var\s+mid\s*=\s*"([^"]+)"'])
    idx = _match(page, [r'idx\s*:\s*"([^"]+)"', r'var\s+idx\s*=\s*"([^"]+)"']) or "1"
    timestamp = _match(page, [
        r'var\s+ct\s*=\s*"(\d+)"',
        r'create_time\s*[:=]\s*"?(\d+)',
        r'ori_create_time\D+(\d{10})',
    ])

    if not title or not account_name or not biz:
        raise ArticleUrlError("页面缺少公众号元数据，可能触发了微信验证或文章已失效")
    try:
        numeric_id = base64.b64decode(biz).decode("ascii")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ArticleUrlError("无法解析公众号唯一标识") from exc
    if not numeric_id.isdigit():
        raise ArticleUrlError("公众号唯一标识格式异常")

    published_at = datetime.now(timezone.utc)
    if timestamp:
        published_at = datetime.fromtimestamp(int(timestamp), timezone.utc)
    external_id = f"wx:{biz}:{mid or parsed.path.rsplit('/', 1)[-1]}:{idx}"
    return ResolvedArticle(
        account_name=account_name,
        source_id=f"MP_WXS_{numeric_id}",
        article=ArticleCandidate(
            external_id=external_id,
            title=title,
            url=url,
            published_at=published_at,
        ),
    )


async def resolve_article_url(url: str, timeout: int, user_agent: str) -> ResolvedArticle:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "mp.weixin.qq.com":
        raise ArticleUrlError("只接受 https://mp.weixin.qq.com/ 的公开文章链接")
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.get(url, headers={"User-Agent": user_agent})
        response.raise_for_status()
    return parse_article_page(str(response.url), response.text)
