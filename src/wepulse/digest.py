from collections import defaultdict
import asyncio
from datetime import datetime
from email.message import EmailMessage
import json
import smtplib
from zoneinfo import ZoneInfo

import httpx

from .config import settings
from .db import Database


def render_digest(database: Database, hours: int = 24) -> str:
    articles = database.recent_articles(hours=hours)
    failures = [account for account in database.list_accounts() if account.last_error]
    now = datetime.now(ZoneInfo(settings.tz))
    lines = [f"# 微信公众号更新 · {now:%Y-%m-%d %H:%M}", ""]
    if not articles:
        lines.append(f"过去 {hours} 小时未发现新增文章。")
    else:
        groups: dict[str, list[dict]] = defaultdict(list)
        for article in articles:
            groups[article["account_name"]].append(article)
        lines.append(f"共 {len(groups)} 个公众号更新，新增 {len(articles)} 篇。")
        for account_name, items in groups.items():
            lines.extend(["", f"## {account_name}", ""])
            for item in items:
                published = datetime.fromisoformat(item["published_at"]).astimezone(ZoneInfo(settings.tz))
                lines.append(f"- [{item['title']}]({item['url']}) · {published:%m-%d %H:%M}")
    if failures:
        lines.extend(["", "## 需要处理的采集失败", ""])
        for account in failures:
            lines.append(f"- **{account.name}**：{account.last_error}")
    return "\n".join(lines)


def _send_email(subject: str, body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from or settings.smtp_username
    message["To"] = settings.email_to
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=settings.request_timeout_seconds) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)


async def send_notifications(markdown: str) -> dict[str, str]:
    results: dict[str, str] = {}
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        if settings.wecom_webhook_url:
            try:
                response = await client.post(
                    settings.wecom_webhook_url,
                    json={"msgtype": "markdown", "markdown": {"content": markdown[:4000]}},
                )
                response.raise_for_status()
                payload = response.json()
                if payload.get("errcode", 0) != 0:
                    raise RuntimeError(payload.get("errmsg", "企业微信返回错误"))
                results["wecom"] = "ok"
            except Exception as exc:
                results["wecom"] = f"error: {exc}"
        if settings.digest_webhook_url:
            try:
                response = await client.post(
                    settings.digest_webhook_url,
                    json={"text": markdown, "format": "markdown"},
                )
                response.raise_for_status()
                results["webhook"] = "ok"
            except Exception as exc:
                results["webhook"] = f"error: {exc}"
    if settings.smtp_host and settings.email_to and (settings.email_from or settings.smtp_username):
        try:
            subject = f"{settings.app_name} 每日更新 · {datetime.now(ZoneInfo(settings.tz)):%Y-%m-%d}"
            await asyncio.to_thread(_send_email, subject, markdown)
            results["email"] = "ok"
        except Exception as exc:
            results["email"] = f"error: {exc}"
    return results


async def publish_digest(database: Database, hours: int = 24) -> str:
    markdown = render_digest(database, hours)
    output = settings.data_dir / "latest_digest.md"
    output.write_text(markdown, encoding="utf-8")
    results = await send_notifications(markdown)
    (settings.data_dir / "last_notification.json").write_text(
        json.dumps({"sent_at": datetime.now().isoformat(), "results": results}, ensure_ascii=False),
        encoding="utf-8",
    )
    return markdown
