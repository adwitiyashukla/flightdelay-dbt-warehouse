import logging
import time

import duckdb

from flightdelay.config import Config, Source

log = logging.getLogger("flightdelay")

AUDIT_TABLE = """
create table if not exists raw.load_audit (
    loaded_at timestamp not null,
    table_name varchar not null,
    month varchar,
    rows bigint not null,
    source_file varchar not null
)
"""


def connect(config: Config) -> duckdb.DuckDBPyConnection:
    config.warehouse_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(config.warehouse_path))
    connection.execute("create schema if not exists raw")
    connection.execute(AUDIT_TABLE)
    return connection


def _quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _read_expr(config: Config, source: Source) -> tuple[str, list]:
    options = ["sample_size=-1", "header=" + ("true" if source.header else "false")]
    parameters: list = [str(config.raw_dir / source.file)]
    if source.nullstr:
        options.append(f"nullstr={_quote(source.nullstr)}")
    if source.columns:
        options.append("names=[" + ", ".join(_quote(column) for column in source.columns) + "]")
    return "read_csv(?, " + ", ".join(options) + ")", parameters


def _audit(connection, source: Source, month: str | None, rows: int) -> None:
    connection.execute(
        "insert into raw.load_audit values (now()::timestamp, ?, ?, ?, ?)",
        [source.name, month, rows, source.file],
    )


def load_full(connection, config: Config, source: Source) -> int:
    expr, parameters = _read_expr(config, source)
    connection.execute(
        f"create or replace table raw.{source.name} as select * from {expr}", parameters
    )
    rows = connection.execute(f"select count(*) from raw.{source.name}").fetchone()[0]
    _audit(connection, source, None, rows)
    return rows


def load_monthly(connection, config: Config, source: Source, months: list[str]) -> int:
    expr, parameters = _read_expr(config, source)
    staged = f"staged_{source.name}"
    connection.execute(f"create or replace temp table {staged} as select * from {expr}", parameters)
    connection.execute(
        f"create table if not exists raw.{source.name} as select * from {staged} limit 0"
    )
    staged_types = connection.execute(f"describe {staged}").fetchall()
    raw_types = connection.execute(f"describe raw.{source.name}").fetchall()
    if [row[:2] for row in staged_types] != [row[:2] for row in raw_types]:
        log.warning("schema changed for raw.%s, rebuilding table", source.name)
        connection.execute(
            f"create or replace table raw.{source.name} as select * from {staged} limit 0"
        )
    total = 0
    for month in months:
        year_part, month_part = (int(part) for part in month.split("-"))
        connection.execute(
            f"delete from raw.{source.name} where year = ? and month = ?", [year_part, month_part]
        )
        connection.execute(
            f"insert into raw.{source.name} select * from {staged} where year = ? and month = ?",
            [year_part, month_part],
        )
        rows = connection.execute(
            f"select count(*) from raw.{source.name} where year = ? and month = ?",
            [year_part, month_part],
        ).fetchone()[0]
        _audit(connection, source, month, rows)
        total += rows
    connection.execute(f"drop table {staged}")
    return total


def load_all(config: Config, months: list[str]) -> dict[str, int]:
    connection = connect(config)
    counts: dict[str, int] = {}
    try:
        for source in config.sources:
            started = time.perf_counter()
            if source.monthly:
                counts[source.name] = load_monthly(connection, config, source, months)
            else:
                counts[source.name] = load_full(connection, config, source)
            log.info(
                "loaded raw.%s (%d rows in %.1fs)",
                source.name,
                counts[source.name],
                time.perf_counter() - started,
            )
    finally:
        connection.close()
    return counts
