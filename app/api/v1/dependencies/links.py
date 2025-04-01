from fastapi import Depends
from redis import Redis

from core.redis import get_redis_client
from db.repositories.links import LinksRepository, get_links_repository
from api.v1.services.links import LinksService


def get_links_service(links_repository: LinksRepository = Depends(get_links_repository)) -> LinksService:
    return LinksService(links_repository=links_repository)
