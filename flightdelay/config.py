import tomllib
from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class HttpSettings:
    timeout_s: float
    retries: int
    backoff_s: float


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    file: str
    monthly: bool = False
    header: bool = True
    nullstr: str = ""
    columns: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Config:
    root: Path
    warehouse_path: Path
    raw_dir: Path
    months: list[str]
    http: HttpSettings
    sources: list[Source]


def _require(table: dict, key: str, kind: type, where: str):
    if key not in table:
        raise ConfigError(f"missing key {key} in {where}")
    value = table[key]
    if kind is float and isinstance(value, int) and not isinstance(value, bool):
        value = float(value)
    if not isinstance(value, kind) or isinstance(value, bool) and kind is not bool:
        raise ConfigError(f"key {key} in {where} must be {kind.__name__}")
    return value


def _valid_month(month: str) -> bool:
    parts = month.split("-")
    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
        return False
    if not (parts[0].isdigit() and parts[1].isdigit()):
        return False
    return 1 <= int(parts[1]) <= 12


def load_config(path: Path) -> Config:
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")
    with open(path, "rb") as handle:
        try:
            raw = tomllib.load(handle)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"config is not valid TOML: {exc}") from exc
    root = path.resolve().parent
    warehouse = _require(raw.get("warehouse", {}), "path", str, "[warehouse]")
    ingest = raw.get("ingest", {})
    raw_dir = _require(ingest, "raw_dir", str, "[ingest]")
    months = _require(ingest, "months", list, "[ingest]")
    if not months:
        raise ConfigError("[ingest] months must not be empty")
    for month in months:
        if not isinstance(month, str) or not _valid_month(month):
            raise ConfigError(f"invalid month {month!r}, expected YYYY-MM")
    if len(set(months)) != len(months):
        raise ConfigError("[ingest] months contains duplicates")
    http_table = raw.get("http", {})
    http = HttpSettings(
        timeout_s=_require(http_table, "timeout_s", float, "[http]"),
        retries=_require(http_table, "retries", int, "[http]"),
        backoff_s=_require(http_table, "backoff_s", float, "[http]"),
    )
    if http.timeout_s <= 0:
        raise ConfigError("[http] timeout_s must be positive")
    if http.retries < 0:
        raise ConfigError("[http] retries must not be negative")
    if http.backoff_s < 0:
        raise ConfigError("[http] backoff_s must not be negative")
    entries = raw.get("sources", [])
    if not entries:
        raise ConfigError("at least one [[sources]] entry is required")
    sources = []
    for entry in entries:
        name = _require(entry, "name", str, "[[sources]]")
        url = _require(entry, "url", str, f"source {name}")
        if not url.startswith("https://"):
            raise ConfigError(f"source {name} url must start with https://")
        columns = entry.get("columns", [])
        if not isinstance(columns, list) or any(not isinstance(c, str) for c in columns):
            raise ConfigError(f"source {name} columns must be a list of strings")
        header = entry.get("header", True)
        if not isinstance(header, bool):
            raise ConfigError(f"source {name} header must be a boolean")
        if not header and not columns:
            raise ConfigError(f"source {name} needs columns when header is false")
        sources.append(
            Source(
                name=name,
                url=url,
                file=_require(entry, "file", str, f"source {name}"),
                monthly=entry.get("monthly", False) is True,
                header=header,
                nullstr=entry.get("nullstr", ""),
                columns=list(columns),
            )
        )
    names = [source.name for source in sources]
    if len(set(names)) != len(names):
        raise ConfigError("source names must be unique")
    return Config(
        root=root,
        warehouse_path=root / warehouse,
        raw_dir=root / raw_dir,
        months=sorted(months),
        http=http,
        sources=sources,
    )
