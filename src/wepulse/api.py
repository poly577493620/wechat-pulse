from contextlib import asynccontextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from secrets import compare_digest

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, HttpUrl

from . import __version__
from .article_url import resolve_article_url
from .config import settings
from .db import Database
from .dashboard import ADMIN_HTML
from .digest import render_digest, send_notifications
from .feeds import rss_xml
from .models import ArticleCandidate
from .scheduler import build_scheduler
from .service import CollectionService

database = Database(settings.database_path)
service = CollectionService(database)
scheduler = build_scheduler(database, service)
ENV_PATH = Path(".env")


@asynccontextmanager
async def lifespan(_: FastAPI):
    database.initialize()
    scheduler.start()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title=settings.app_name, version=__version__, lifespan=lifespan)
admin_bearer = HTTPBearer(auto_error=False)


def require_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(admin_bearer),
) -> None:
    if settings.admin_token == "change-me":
        raise HTTPException(status_code=503, detail="请先修改 ADMIN_TOKEN")
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not compare_digest(credentials.credentials, settings.admin_token)
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的管理令牌")


class AccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    connector: str = Field(pattern="^(rss|weread)$")
    source_id: str | None = Field(default=None, max_length=300)
    feed_url: HttpUrl | None = None


class ManualImport(BaseModel):
    account_name: str = Field(min_length=1, max_length=120)
    url: HttpUrl
    title: str = Field(min_length=1, max_length=500)
    published_at: datetime | None = None


class ArticleUrlSubscribe(BaseModel):
    url: HttpUrl


class WeReadCookieUpdate(BaseModel):
    cookie: str = Field(min_length=1, max_length=32768)


def _save_env_value(key: str, value: str) -> None:
    """Update one dotenv value without exposing it in API responses or logs."""
    try:
        content = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
        lines = content.splitlines()
        replacement = f"{key}={value}"
        updated = False
        for index, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[index] = replacement
                updated = True
                break
        if not updated:
            lines.append(replacement)
        temporary = ENV_PATH.with_name(f"{ENV_PATH.name}.tmp")
        temporary.write_text("\n".join(lines) + "\n", encoding="utf-8")
        temporary.replace(ENV_PATH)
    except OSError as exc:
        raise HTTPException(500, "无法写入 .env，请检查项目文件夹修改权限") from exc


@app.get("/", include_in_schema=False)
def index() -> RedirectResponse:
    return RedirectResponse("/admin")


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
def admin_page() -> str:
    return ADMIN_HTML


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__, "database": str(settings.database_path)}


@app.get("/api/accounts")
def list_accounts() -> list[dict]:
    return [asdict(account) for account in database.list_accounts()]


@app.get("/api/status", dependencies=[Depends(require_admin)])
def system_status() -> dict:
    accounts = database.list_accounts()
    weread_accounts = [account for account in accounts if account.connector == "weread"]
    weread_errors = [account.last_error for account in weread_accounts if account.last_error]
    if not settings.weread_cookie:
        cookie = {"status": "missing", "label": "未配置"}
    elif any("cookie" in error.lower() or "login" in error.lower() or "401" in error for error in weread_errors):
        cookie = {"status": "error", "label": "可能已失效"}
    elif any(account.last_checked_at and not account.last_error for account in weread_accounts):
        cookie = {"status": "ok", "label": "最近验证成功"}
    else:
        cookie = {"status": "unknown", "label": "已配置待验证"}
    notification_path = settings.data_dir / "last_notification.json"
    last_notification = None
    if notification_path.exists():
        try:
            last_notification = json.loads(notification_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "version": __version__,
        "accounts": {"total": len(accounts), "failed": sum(bool(a.last_error) for a in accounts)},
        "weread": cookie,
        "schedule": {"timezone": settings.tz, "hour": settings.digest_hour, "minute": settings.digest_minute},
        "notifications": {
            "wecom": bool(settings.wecom_webhook_url),
            "email": bool(settings.smtp_host and settings.email_to),
            "webhook": bool(settings.digest_webhook_url),
            "last": last_notification,
        },
    }


@app.post("/api/accounts", dependencies=[Depends(require_admin)], status_code=201)
def create_account(payload: AccountCreate) -> dict:
    if payload.connector == "rss" and not payload.feed_url:
        raise HTTPException(422, "RSS 采集器需要 feed_url")
    if payload.connector == "weread" and not payload.source_id:
        raise HTTPException(422, "微信读书采集器需要 source_id/bookId")
    try:
        account_id = database.add_account(
            payload.name, payload.connector, payload.source_id,
            str(payload.feed_url) if payload.feed_url else None,
        )
    except Exception as exc:
        raise HTTPException(409, f"订阅已存在或数据无效：{exc}") from exc
    return {"id": account_id}


@app.delete("/api/accounts/{account_id}", dependencies=[Depends(require_admin)])
def delete_account(account_id: int) -> dict:
    if not database.delete_account(account_id):
        raise HTTPException(404, "订阅不存在")
    return {"deleted": True, "account_id": account_id}


@app.post("/api/accounts/{account_id}/collect", dependencies=[Depends(require_admin)])
async def collect_account(account_id: int) -> dict:
    account = database.get_account(account_id)
    if not account:
        raise HTTPException(404, "订阅不存在")
    return await service.collect_account(account)


@app.post("/api/collect", dependencies=[Depends(require_admin)])
async def collect_all() -> list[dict]:
    return await service.collect_all()


@app.post("/api/checks/weread", dependencies=[Depends(require_admin)])
async def check_weread_cookie() -> dict:
    if not settings.weread_cookie:
        return {"status": "error", "message": "未配置 WEREAD_COOKIE"}
    account = next((item for item in database.list_accounts(True) if item.connector == "weread"), None)
    if account is None:
        return {"status": "unknown", "message": "Cookie 已配置；请先添加一个微信原文订阅以执行真实验证"}
    result = await service.collect_account(account)
    if result.get("error"):
        return {"status": "error", "message": f"Cookie 或采集接口验证失败：{result['error']}"}
    return {"status": "ok", "message": f"Cookie 验证成功：{account.name}", "result": result}


@app.put("/api/config/weread-cookie", dependencies=[Depends(require_admin)])
def update_weread_cookie(payload: WeReadCookieUpdate) -> dict:
    cookie = payload.cookie.strip()
    if cookie.lower().startswith("cookie:"):
        cookie = cookie.split(":", 1)[1].strip()
    if any(ord(character) < 32 or ord(character) == 127 for character in cookie):
        raise HTTPException(422, "Cookie 含有换行或不可见控制字符，请重新从请求标头复制完整值")
    fields = {
        part.split("=", 1)[0].strip()
        for part in cookie.split(";")
        if "=" in part and part.split("=", 1)[0].strip()
    }
    missing = sorted({"wr_vid", "wr_skey"} - fields)
    if missing:
        raise HTTPException(422, f"Cookie 不完整，缺少：{', '.join(missing)}")

    _save_env_value("WEREAD_COOKIE", cookie)
    settings.weread_cookie = cookie
    collector = service.collectors.get("weread")
    if collector is not None:
        collector.cookie = cookie
    return {
        "status": "ok",
        "configured": True,
        "field_count": len(fields),
        "message": "Cookie 已安全保存并立即生效；页面不会回显其内容",
    }


@app.post("/api/notifications/test", dependencies=[Depends(require_admin)])
async def test_notifications() -> dict:
    markdown = render_digest(database, 24)
    results = await send_notifications(markdown)
    return {"ok": bool(results) and all(value == "ok" for value in results.values()), "results": results}


@app.post("/api/import", dependencies=[Depends(require_admin)], status_code=201)
def import_article(payload: ManualImport) -> dict:
    account = database.find_account_by_name(payload.account_name)
    if not account:
        account_id = database.add_account(payload.account_name, "manual", None, None)
        account = database.get_account(account_id)
    assert account is not None
    url = str(payload.url)
    article = ArticleCandidate(
        external_id=sha256(url.encode()).hexdigest(),
        title=payload.title,
        url=url,
        published_at=payload.published_at or datetime.now(timezone.utc),
    )
    return {"inserted": database.insert_article(account.id, article), "account_id": account.id}


@app.post("/api/accounts/from-article", dependencies=[Depends(require_admin)], status_code=201)
async def create_account_from_article(payload: ArticleUrlSubscribe) -> dict:
    try:
        resolved = await resolve_article_url(
            str(payload.url), settings.request_timeout_seconds, settings.user_agent
        )
    except Exception as exc:
        raise HTTPException(422, f"无法识别微信文章：{exc}") from exc
    account = database.find_account_by_name(resolved.account_name)
    created = account is None
    if account is None:
        try:
            account_id = database.add_account(
                resolved.account_name, "weread", resolved.source_id, None
            )
            account = database.get_account(account_id)
        except Exception as exc:
            raise HTTPException(409, f"公众号已存在或数据冲突：{exc}") from exc
    assert account is not None
    inserted = database.insert_article(account.id, resolved.article)
    return {
        "account_id": account.id,
        "account_name": account.name,
        "source_id": account.source_id,
        "account_created": created,
        "baseline_article_inserted": inserted,
        "title": resolved.article.title,
        "published_at": resolved.article.published_at,
    }


@app.get("/api/articles")
def articles(hours: int = Query(default=24, ge=1, le=24 * 365), account_id: int | None = None) -> list[dict]:
    return database.recent_articles(hours=hours, account_id=account_id)


@app.get("/api/digest")
def digest(hours: int = Query(default=24, ge=1, le=24 * 31)) -> Response:
    return Response(render_digest(database, hours), media_type="text/markdown; charset=utf-8")


@app.get("/feeds/all.xml")
def all_feed(hours: int = Query(default=24 * 30, ge=1, le=24 * 365)) -> Response:
    xml = rss_xml(settings.app_name, database.recent_articles(hours=hours))
    return Response(xml, media_type="application/rss+xml; charset=utf-8")


@app.get("/feeds/{account_id}.xml")
def account_feed(account_id: int, hours: int = Query(default=24 * 30, ge=1, le=24 * 365)) -> Response:
    account = database.get_account(account_id)
    if not account:
        raise HTTPException(404, "订阅不存在")
    xml = rss_xml(account.name, database.recent_articles(hours=hours, account_id=account_id))
    return Response(xml, media_type="application/rss+xml; charset=utf-8")
