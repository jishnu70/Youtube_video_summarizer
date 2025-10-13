# src/presentation/container.py

from src.application.use_case import UseCase
from src.infrastructure.mongo_service import MongoService
from src.infrastructure.redis_client import get_redis_client
from src.infrastructure.video_repository_imp import VideoRepositoryImp
from src.infrastructure.system_config import config

async def get_use_case():
    video_repo_impl = VideoRepositoryImp(config.DATABASE_URL)
    await video_repo_impl.connect_db()
    r_client = get_redis_client()
    m_client = MongoService(config.DATABASE_URL)
    repo_use_case = UseCase(video_repo_impl, r_client, m_client)
    return repo_use_case
