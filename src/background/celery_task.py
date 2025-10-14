# src/background/celery_task.py

import asyncio
from billiard.exceptions import SoftTimeLimitExceeded
from src.application.video_pipeline_service import VideoPipelineService
from src.domain.model_exceptions import SoftTimeLimitExceededError
from src.infrastructure.mongo_service import MongoService
from src.infrastructure.redis_client import get_redis_client
from src.infrastructure.system_config import config
from src.infrastructure.video_repository_imp import VideoRepositoryImp
from src.infrastructure.correction_service import Correction_Service
from src.infrastructure.stt_service import STTService
from src.infrastructure.summarizer_service import SummarizerService
from src.infrastructure.yt_service import YoutubeService
from src.background.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="summarize_video_task", max_retries=3, default_retry_delay=60, ignore_result=False)
def queue_yt_video(self, url: str):
    """
    Celery task to summarize a YouTube video.
    This function runs synchronously but executes async code inside an event loop.
    """

    logger.info("Entered the Celery queue")
    redis_client = get_redis_client()
    async def run_pipeline():
        logger.info("Running the asynchronous run_pipeline method")
        # Initialize services
        yt_service = YoutubeService()
        stt_service = STTService()
        correction_service = Correction_Service()
        summarizer_service = SummarizerService()
        video_repo = VideoRepositoryImp(config.DATABASE_URL)
        mongo = MongoService(uri=config.DATABASE_URL)
        await mongo.run_init()

        await mongo.update_status(self.request.id, "STARTED")
        try:
            # the actual video processing pipeline
            vid_pipline = VideoPipelineService(
                yt_service,
                stt_service,
                correction_service,
                summarizer_service,
            )

            video_response = await vid_pipline.transform_the_video(url=url)

            saved_response = await video_repo.save(video_response)
            await redis_client.set_cache_summary(saved_response)
            await mongo.update_status(self.request.id, "SUCCESS")

            return self.request.id

        except SoftTimeLimitExceeded:
            logger.exception(f"Task {self.request.id} timed out for URL {url}")
            await mongo.update_status(self.request.id, "TIMEOUT")
            raise SoftTimeLimitExceededError(f"Task {self.request.id} timed out for URL {url}")
        except Exception as e:
            logger.exception(f"Task {self.request.id} failed out for URL {url} for: {e}")
            await mongo.update_status(self.request.id, "FAILED")
            raise
        finally:
            await redis_client.delete_queued_task(url)

    try:
        return asyncio.run(run_pipeline())
    except Exception as e:
        logger.error(f"Celery task {self.request.id} failed: {e}")
        raise Exception("failed to start the distributed task")
