import duckdb
import pytest

from flightdelay.config import load_config
from flightdelay.load import load_all


@pytest.fixture
def loaded(config_path, raw_dir):
    config = load_config(config_path)
    counts = load_all(config, config.months)
    connection = duckdb.connect(str(config.warehouse_path), read_only=True)
    yield config, counts, connection
    connection.close()


def test_loads_all_tables(loaded):
    _, counts, _ = loaded
    assert counts["flights"] == 3
    assert counts["planes"] == 2
    assert counts["airports"] == 4
    assert counts["ourairports_airports"] == 5
    assert counts["openflights_airlines"] == 3


def test_empty_strings_become_nulls(loaded):
    _, _, connection = loaded
    row = connection.execute(
        "select dep_time, dep_delay, arr_delay from raw.flights where rownames = 3"
    ).fetchone()
    assert row == (None, None, None)


def test_numeric_columns_keep_numeric_types(loaded):
    _, _, connection = loaded
    types = dict(
        connection.execute(
            "select column_name, data_type from information_schema.columns "
            "where table_schema = 'raw' and table_name = 'flights'"
        ).fetchall()
    )
    assert types["dep_time"] == "BIGINT"
    assert types["arr_delay"] == "BIGINT"


def test_headerless_source_uses_configured_columns(loaded):
    _, _, connection = loaded
    columns = [
        row[0]
        for row in connection.execute(
            "select column_name from information_schema.columns "
            "where table_schema = 'raw' and table_name = 'openflights_airlines' "
            "order by ordinal_position"
        ).fetchall()
    ]
    assert columns[:4] == ["airline_id", "name", "alias", "iata"]


def test_audit_rows_written(loaded):
    config, _, connection = loaded
    monthly = connection.execute(
        "select count(*) from raw.load_audit where table_name = 'flights'"
    ).fetchone()[0]
    assert monthly == len(config.months)
    snapshot = connection.execute(
        "select count(*) from raw.load_audit where table_name = 'planes' and month is null"
    ).fetchone()[0]
    assert snapshot == 1


def test_rerun_is_idempotent(config_path, raw_dir):
    config = load_config(config_path)
    load_all(config, config.months)
    load_all(config, config.months)
    connection = duckdb.connect(str(config.warehouse_path), read_only=True)
    try:
        assert connection.execute("select count(*) from raw.flights").fetchone()[0] == 3
        assert connection.execute("select count(*) from raw.planes").fetchone()[0] == 2
    finally:
        connection.close()


def test_single_month_reload_leaves_other_months(config_path, raw_dir):
    config = load_config(config_path)
    load_all(config, config.months)
    load_all(config, ["2013-02"])
    connection = duckdb.connect(str(config.warehouse_path), read_only=True)
    try:
        by_month = dict(
            connection.execute("select month, count(*) from raw.flights group by 1").fetchall()
        )
        assert by_month == {1: 2, 2: 1}
    finally:
        connection.close()


def test_partial_month_selection_loads_only_that_month(config_path, raw_dir):
    config = load_config(config_path)
    load_all(config, ["2013-01"])
    connection = duckdb.connect(str(config.warehouse_path), read_only=True)
    try:
        assert connection.execute("select count(*) from raw.flights").fetchone()[0] == 2
    finally:
        connection.close()
