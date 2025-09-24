from src.application.use_case import UseCase
from src.infrastructure.video_repository_imp import VideoRepositoryImp
from src.infrastructure.system_config import config

def get_use_case():
    video_repo_impl = VideoRepositoryImp(config.DATABASE_URL)
    repo_use_case = UseCase(video_repo_impl)
    return repo_use_case
