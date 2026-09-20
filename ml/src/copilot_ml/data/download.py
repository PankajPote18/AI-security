"""Checksummed dataset download.

The first successful download pins the archive's SHA-256 in `datasets/checksums.json`
(tracked in git). Every later run verifies the file against that pin, so a silently
changed or corrupted dataset fails loudly instead of changing results.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import urllib.request
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlsplit

from copilot_ml.config import MLSettings
from copilot_ml.data.sources import DatasetSource

logger = logging.getLogger(__name__)

_CHUNK_BYTES = 1024 * 1024
_LOG_EVERY_BYTES = 5 * _CHUNK_BYTES


class ChecksumMismatchError(RuntimeError):
    """The archive on disk does not match the checksum pinned for this dataset."""


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_or_pin_checksum(archive: Path, key: str, checksums_path: Path) -> str:
    """Return the archive's SHA-256, pinning it on first use and verifying afterwards."""
    actual = sha256_of(archive)
    pins: dict[str, str] = {}
    if checksums_path.exists():
        pins = json.loads(checksums_path.read_text(encoding="utf-8"))

    expected = pins.get(key)
    if expected is None:
        pins[key] = actual
        checksums_path.parent.mkdir(parents=True, exist_ok=True)
        checksums_path.write_text(json.dumps(pins, indent=2, sort_keys=True) + "\n", "utf-8")
        logger.info("Pinned checksum for %s: %s", key, actual)
    elif expected != actual:
        raise ChecksumMismatchError(
            f"{archive.name}: sha256 {actual} != pinned {expected}. "
            "Delete the file to re-download, or update the pin only if the change is intended."
        )
    return actual


def _download(url: str, dest: Path, allowed_schemes: Sequence[str], retries: int = 3) -> None:
    scheme = urlsplit(url).scheme
    if scheme not in allowed_schemes:
        raise ValueError(f"Refusing to download over scheme {scheme!r}; allowed: {allowed_schemes}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_name(dest.name + ".part")
    for attempt in range(1, retries + 1):
        try:
            logger.info("Downloading %s (attempt %d/%d)", url, attempt, retries)
            # Scheme is validated against an allow-list above, so S310 does not apply.
            with urllib.request.urlopen(url, timeout=60) as response, partial.open("wb") as out:  # noqa: S310
                received = 0
                while chunk := response.read(_CHUNK_BYTES):
                    out.write(chunk)
                    received += len(chunk)
                    if received % _LOG_EVERY_BYTES < _CHUNK_BYTES:
                        logger.info("  ...%.1f MB", received / 1e6)
            partial.replace(dest)
            return
        except OSError as error:
            logger.warning("Download failed: %s", error)
            if attempt == retries:
                raise
            time.sleep(2**attempt)


def ensure_archive(
    source: DatasetSource,
    settings: MLSettings,
    allowed_schemes: Sequence[str] = ("https",),
) -> tuple[Path, str]:
    """Make sure the verified dataset archive exists locally. Returns (path, sha256)."""
    archive = settings.raw_dir / f"{source.key}.zip"
    if not archive.exists():
        _download(source.download_url, archive, allowed_schemes)
    checksum = verify_or_pin_checksum(archive, source.key, settings.checksums_path)
    return archive, checksum
