import argparse
import logging
import sys
from pathlib import Path

import duckdb

from flightdelay.config import Config, ConfigError, load_config
from flightdelay.download import DownloadError, download_all
from flightdelay.load import load_all


def _parse_months(value: str, config: Config) -> list[str]:
    if value == "all":
        return config.months
    months = [month.strip() for month in value.split(",") if month.strip()]
    unknown = [month for month in months if month not in config.months]
    if unknown:
        raise ConfigError(f"months not in config: {', '.join(unknown)}")
    return sorted(set(months))


def _status(config: Config) -> None:
    if not config.warehouse_path.is_file():
        print("warehouse not created yet")
        return
    connection = duckdb.connect(str(config.warehouse_path), read_only=True)
    try:
        tables = connection.execute(
            "select table_name from information_schema.tables "
            "where table_schema = 'raw' and table_name <> 'load_audit' order by table_name"
        ).fetchall()
        for (table,) in tables:
            rows = connection.execute(f"select count(*) from raw.{table}").fetchone()[0]
            print(f"raw.{table}: {rows} rows")
        audit = connection.execute(
            "select loaded_at, table_name, coalesce(month, '-'), rows "
            "from raw.load_audit order by loaded_at desc limit 10"
        ).fetchall()
        for loaded_at, table, month, rows in audit:
            print(f"{loaded_at} {table} {month} {rows}")
    finally:
        connection.close()


def build_parser() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--config", default="config.toml", type=Path)
    shared.add_argument("--quiet", action="store_true")
    parser = argparse.ArgumentParser(prog="flightdelay")
    commands = parser.add_subparsers(dest="command", required=True)
    ingest = commands.add_parser("ingest", parents=[shared])
    ingest.add_argument("--months", default="all")
    ingest.add_argument("--refresh", action="store_true")
    ingest.add_argument("--skip-download", action="store_true")
    commands.add_parser("status", parents=[shared])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    try:
        config = load_config(args.config)
        if args.command == "ingest":
            months = _parse_months(args.months, config)
            if not args.skip_download:
                download_all(config, refresh=args.refresh)
            counts = load_all(config, months)
            print(f"loaded {sum(counts.values())} rows across {len(counts)} raw tables")
        elif args.command == "status":
            _status(config)
    except (ConfigError, DownloadError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
