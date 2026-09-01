import httpx
import pytest

from flightdelay.cli import main
from tests.conftest import RESPONSES


def _patch(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        name = request.url.path.lstrip("/")
        return httpx.Response(200, text=RESPONSES[name])

    transport = httpx.MockTransport(handler)
    original = httpx.Client.__init__

    def patched(self, *args, **kwargs):
        kwargs["transport"] = transport
        original(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", patched)


def test_ingest_runs_end_to_end(monkeypatch, config_path, capsys):
    _patch(monkeypatch)
    assert main(["ingest", "--config", str(config_path)]) == 0
    assert "loaded" in capsys.readouterr().out


def test_ingest_with_skip_download(config_path, raw_dir, capsys):
    assert main(["ingest", "--config", str(config_path), "--skip-download"]) == 0
    assert "loaded" in capsys.readouterr().out


def test_ingest_rejects_unknown_month(config_path, raw_dir, capsys):
    code = main(["ingest", "--config", str(config_path), "--months", "2014-01", "--skip-download"])
    assert code == 1
    assert "not in config" in capsys.readouterr().err


def test_status_before_any_load(config_path, capsys):
    assert main(["status", "--config", str(config_path)]) == 0
    assert "not created yet" in capsys.readouterr().out


def test_status_after_load(config_path, raw_dir, capsys):
    main(["ingest", "--config", str(config_path), "--skip-download"])
    capsys.readouterr()
    assert main(["status", "--config", str(config_path)]) == 0
    out = capsys.readouterr().out
    assert "raw.flights: 3 rows" in out


def test_missing_config_returns_error(tmp_path, capsys):
    assert main(["ingest", "--config", str(tmp_path / "absent.toml")]) == 1
    assert "error:" in capsys.readouterr().err


def test_requires_a_command(capsys):
    with pytest.raises(SystemExit):
        main([])
