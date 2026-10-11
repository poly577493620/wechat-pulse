import asyncio
import logging

from .collectors import RssCollector, WeReadCollector
from .collectors.base import CollectorError
from .config import settings
from .db import Database
from .models import Account

logger = logging.getLogger(__name__)


class CollectionService:
    def __init__(self, database: Database):
        self.database = database
        self.collectors = {
            "rss": RssCollector(settings.request_timeout_seconds, settings.user_agent),
            "weread": WeReadCollector(
                settings.weread_cookie,
                settings.request_timeout_seconds,
                settings.user_agent,
                settings.weread_content,
            ),
        }

    async def collect_account(self, account: Account) -> dict:
        collector = self.collectors.get(account.connector)
        if not collector:
            error = f"不支持的采集器：{account.connector}"
            self.database.set_account_state(account.id, error)
            return {"account_id": account.id, "inserted": 0, "error": error}
        try:
            candidates = await collector.collect(account)
            inserted = sum(self.database.insert_article(account.id, article) for article in candidates)
            self.database.set_account_state(account.id, None)
            return {"account_id": account.id, "fetched": len(candidates), "inserted": inserted, "error": None}
        except (CollectorError, Exception) as exc:
            error = str(exc)[:1000]
            logger.warning("Collection failed for %s: %s", account.name, error)
            self.database.set_account_state(account.id, error)
            return {"account_id": account.id, "inserted": 0, "error": error}

    async def collect_all(self) -> list[dict]:
        accounts = self.database.list_accounts(enabled_only=True)
        results: list[dict] = []
        for account in accounts:
            results.append(await self.collect_account(account))
            await asyncio.sleep(1)
        return results
