import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .config import settings
from .db import Database
from .digest import publish_digest
from .service import CollectionService

logger = logging.getLogger(__name__)


async def collect_and_publish(database: Database, service: CollectionService) -> None:
    await service.collect_all()
    await publish_digest(database, 24)


def build_scheduler(database: Database, service: CollectionService) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.tz)
    scheduler.add_job(
        service.collect_all,
        IntervalTrigger(minutes=max(15, settings.collect_interval_minutes)),
        id="collect-all",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    scheduler.add_job(
        collect_and_publish,
        CronTrigger(hour=settings.digest_hour, minute=settings.digest_minute, timezone=settings.tz),
        args=[database, service],
        id="daily-digest",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    return scheduler
