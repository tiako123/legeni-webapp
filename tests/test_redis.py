import sys
import types

from app import RedisCounter, build_counter


class FakeRedis:
    def __init__(self, host, port, password=None, socket_timeout=2):
        self.value = 0

    def incr(self, key):
        self.value += 1
        return self.value

    def ping(self):
        return True


class BrokenRedis(FakeRedis):
    def ping(self):
        raise ConnectionError("redis indisponible")


def use_fake(monkeypatch, cls):
    monkeypatch.setitem(sys.modules, "redis", types.SimpleNamespace(Redis=cls))


def test_redis_counter(monkeypatch):
    use_fake(monkeypatch, FakeRedis)
    counter = RedisCounter("redis", 6379, "secret")
    assert counter.incr() == 1
    assert counter.ping() is True
    assert counter.name == "redis"


def test_redis_ping_failure(monkeypatch):
    use_fake(monkeypatch, BrokenRedis)
    assert RedisCounter("redis", 6379).ping() is False


def test_build_counter_uses_redis(monkeypatch):
    use_fake(monkeypatch, FakeRedis)
    monkeypatch.setenv("REDIS_HOST", "redis")
    assert build_counter().name == "redis"


def test_build_counter_memory_by_default(monkeypatch):
    monkeypatch.delenv("REDIS_HOST", raising=False)
    assert build_counter().name == "memoire"
