import pytest

from flightdelay.config import ConfigError, load_config


def test_loads_valid_config(config_path):
    config = load_config(config_path)
    assert len(config.sources) == 7
    assert config.months == ["2013-01", "2013-02"]
    assert config.http.retries == 2
    assert config.warehouse_path.name == "flightdelay.duckdb"
    assert config.raw_dir.is_absolute()


def test_sources_keep_declared_flags(config_path):
    config = load_config(config_path)
    by_name = {source.name: source for source in config.sources}
    assert by_name["flights"].monthly is True
    assert by_name["planes"].monthly is False
    assert by_name["openflights_airlines"].header is False
    assert by_name["openflights_airlines"].columns[0] == "airline_id"


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "absent.toml")


def test_invalid_toml_raises(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[warehouse\n")
    with pytest.raises(ConfigError, match="not valid TOML"):
        load_config(path)


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        ('months = ["2013-13"]', "invalid month"),
        ('months = ["2013-1"]', "invalid month"),
        ('months = ["2013-01", "2013-01"]', "duplicates"),
        ("months = []", "must not be empty"),
    ],
)
def test_month_validation(config_path, bad, message):
    text = config_path.read_text().replace('months = ["2013-01", "2013-02"]', bad)
    config_path.write_text(text)
    with pytest.raises(ConfigError, match=message):
        load_config(config_path)


def test_rejects_negative_retries(config_path):
    config_path.write_text(config_path.read_text().replace("retries = 2", "retries = -1"))
    with pytest.raises(ConfigError, match="retries"):
        load_config(config_path)


def test_rejects_zero_timeout(config_path):
    config_path.write_text(config_path.read_text().replace("timeout_s = 5.0", "timeout_s = 0.0"))
    with pytest.raises(ConfigError, match="timeout_s"):
        load_config(config_path)


def test_rejects_insecure_url(config_path):
    text = config_path.read_text().replace(
        'url = "https://example.test/flights.csv"', 'url = "http://example.test/flights.csv"'
    )
    config_path.write_text(text)
    with pytest.raises(ConfigError, match="https"):
        load_config(config_path)


def test_rejects_duplicate_source_names(config_path):
    text = config_path.read_text().replace('name = "planes"', 'name = "flights"')
    config_path.write_text(text)
    with pytest.raises(ConfigError, match="unique"):
        load_config(config_path)


def test_rejects_headerless_source_without_columns(config_path):
    columns_line = (
        'columns = ["airline_id", "name", "alias", "iata",'
        ' "icao", "callsign", "country", "active"]'
    )
    text = config_path.read_text().replace(columns_line, "")
    config_path.write_text(text)
    with pytest.raises(ConfigError, match="columns when header is false"):
        load_config(config_path)


def test_rejects_missing_warehouse_path(config_path):
    text = config_path.read_text().replace('path = "data/flightdelay.duckdb"', "")
    config_path.write_text(text)
    with pytest.raises(ConfigError, match="missing key path"):
        load_config(config_path)
