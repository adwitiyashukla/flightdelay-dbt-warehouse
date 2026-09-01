import logging
import time
from pathlib import Path

import httpx

from flightdelay.config import Config, Source

log = logging.getLogger("flightdelay")


class DownloadError(Exception):
    pass


def fetch(client: httpx.Client, source: Source, dest: Path, retries: int, backoff_s: float) -> int:
    attempt = 0
    while True:
        try:
            response = client.get(source.url)
            if response.status_code >= 500:
                raise DownloadError(f"{source.name}: server returned {response.status_code}")
            if response.status_code != 200:
                raise DownloadError(f"{source.name}: unexpected status {response.status_code}")
            tmp = dest.with_suffix(dest.suffix + ".part")
            tmp.write_bytes(response.content)
            tmp.replace(dest)
            return len(response.content)
        except (httpx.TransportError, DownloadError):
            attempt += 1
            if attempt > retries:
                raise
            wait = backoff_s * (2 ** (attempt - 1))
            log.warning("retry %d for %s in %.1fs", attempt, source.name, wait)
            time.sleep(wait)


def download_all(config: Config, refresh: bool = False) -> dict[str, int]:
    config.raw_dir.mkdir(parents=True, exist_ok=True)
    sizes: dict[str, int] = {}
    with httpx.Client(timeout=config.http.timeout_s, follow_redirects=True) as client:
        for source in config.sources:
            dest = config.raw_dir / source.file
            if dest.is_file() and not refresh:
                sizes[source.name] = dest.stat().st_size
                log.info("cached %s (%d bytes)", source.file, sizes[source.name])
                continue
            started = time.perf_counter()
            size = fetch(client, source, dest, config.http.retries, config.http.backoff_s)
            sizes[source.name] = size
            elapsed = time.perf_counter() - started
            log.info("downloaded %s (%d bytes in %.1fs)", source.file, size, elapsed)
    return sizes
