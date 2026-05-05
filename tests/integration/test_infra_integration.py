import pytest
import redis

from config import get_settings


@pytest.mark.integration
def test_redis_is_reachable():
    settings = get_settings()
    client = redis.Redis.from_url(settings.redis_url)
    assert client.ping() is True
