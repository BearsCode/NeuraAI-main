import asyncio
import logging
from redis.asyncio import Redis
from redis.exceptions import ResponseError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.app.core.configs import settings
from backend.app.core.database import close_database, init_database, database_manager
from backend.app.db.enums import PublicationStatus, ContentStatus
from backend.app.db.publication import Publication

logger = logging.getLogger("neuaraai.worker")

async def process_publication(publication_id: str) -> None:
    async with database_manager.session_factory() as session:
        publication = await session.scalar(
            select(Publication)
            .options(selectinload(Publication.content_item))
            .where(Publication.id == publication_id)
        )
        if not publication:
            logger.warning(f"Publication not found: {publication_id}")
            return

        if publication.status != PublicationStatus.QUEUED:
            logger.warning(f"Publication {publication_id} is not queued: status is {publication.status}")
            return

        try:
            publication.status = PublicationStatus.PUBLISHED
            if publication.content_item:
                publication.content_item.status = ContentStatus.PUBLISHED
            await session.commit()
            logger.info(f"Successfully published publication: {publication_id}")
        except Exception as exc:
            publication.status = PublicationStatus.FAILED
            publication.last_error_message = str(exc)
            await session.commit()
            logger.error(f"Failed to publish {publication_id}: {exc}")

async def main() -> None:
    if settings.queue_backend != "redis":
        logger.error("QUEUE_BACKEND is not set to redis. Worker exiting.")
        return

    await init_database()

    redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    stream_name = "publication_queue"
    group_name = "publication_group"
    consumer_name = "worker_primary"

    try:
        await redis_client.xgroup_create(stream_name, group_name, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise

    logger.info("Worker started, listening to stream...")

    try:
        while True:
            try:
                response = await redis_client.xreadgroup(
                    groupname=group_name,
                    consumername=consumer_name,
                    streams={stream_name: ">"},
                    count=1,
                    block=5000,
                )
                if not response:
                    continue

                for _, messages in response:
                    for message_id, data in messages:
                        pub_id = data.get("publication_id")
                        if pub_id:
                            await process_publication(pub_id)
                        await redis_client.xack(stream_name, group_name, message_id)
            except Exception as exc:
                logger.error(f"Error in worker read loop: {exc}")
                await asyncio.sleep(5)
    finally:
        await redis_client.aclose()
        await close_database()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    asyncio.run(main())
