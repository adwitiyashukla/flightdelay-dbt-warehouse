import httpx
import pytest

from flightdelay.config import load_config
from flightdelay.download import DownloadError, download_all
from tests.conftest import RESPONSES


def _handler(request: httpx.Request) -> httpx.Response:
    name = request.url.path.lstrip("/")
    if name not in RESPONSES:
        return httpx.Response(404)
    return httpx.Response(200, text=RESPONSES[name])


def _patch(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    original = httpx.Client.__init__

    def patched(self, *args, **kwargs):
        kwargs["transport"] = transport
        original(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", patched)


def test_downloads_every_source(monkeypatch, config_path):
    _patch(monkeypatch, _handler)
    config = load_config(config_path)
    sizes = download_all(config)
    assert set(sizes) == {source.name for source in config.sources}
    assert all(size > 0 for size in sizes.values())
    assert (config.raw_dir / "flights.csv").is_file()


def test_uses_cache_on_second_call(monkeypatch, config_path):
    calls = []

    def counting(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return _handler(request)

    _patch(monkeypatch, counting)
    config = load_config(config_path)
    download_all(config)
    download_all(config)
    assert len(calls) == len(RESPONSES)


def test_refresh_redownloads(monkeypatch, config_path):
    calls = []

    def counting(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        return _handler(request)

    _patch(monkeypatch, counting)
    config = load_config(config_path)
    download_all(config)
    download_all(config, refresh=True)
    assert len(calls) == 2 * len(RESPONSES)


def test_retries_then_succeeds(monkeypatch, config_path):
    attempts = {"count": 0}

    def flaky(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        if attempts["count"] == 1:
            return httpx.Response(503)
        return _handler(request)

    _patch(monkeypatch, flaky)
    config = load_config(config_path)
    sizes = download_all(config)
    assert attempts["count"] == len(RESPONSES) + 1
    assert sizes["flights"] > 0


def test_raises_after_exhausting_retries(monkeypatch, config_path):
    _patch(monkeypatch, lambda request: httpx.Response(500))
    config = load_config(config_path)
    with pytest.raises(DownloadError):
        download_all(config)


def test_leaves_no_partial_file_on_failure(monkeypatch, config_path):
    _patch(monkeypatch, lambda request: httpx.Response(500))
    config = load_config(config_path)
    with pytest.raises(DownloadError):
        download_all(config)
    assert not (config.raw_dir / "flights.csv").exists()
    assert not list(config.raw_dir.glob("*.part"))
