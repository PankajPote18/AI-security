import dataclasses
import functools
import json
import threading
from collections.abc import Iterator
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from copilot_ml.config import MLSettings
from copilot_ml.data.download import (
    ChecksumMismatchError,
    ensure_archive,
    sha256_of,
    verify_or_pin_checksum,
)
from copilot_ml.data.sources import PHIUSIIL
from fixture_data import write_fixture_archive


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def local_server(tmp_path: Path) -> Iterator[str]:
    served = tmp_path / "served"
    write_fixture_archive(served / "fixture.zip")
    handler = functools.partial(_QuietHandler, directory=str(served))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}/fixture.zip"
    server.shutdown()
    server.server_close()


def test_first_use_pins_and_second_use_verifies(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    archive.write_bytes(b"content")
    pins = tmp_path / "checksums.json"

    first = verify_or_pin_checksum(archive, "demo", pins)
    assert json.loads(pins.read_text()) == {"demo": first}
    assert verify_or_pin_checksum(archive, "demo", pins) == first == sha256_of(archive)


def test_tampered_archive_is_rejected(tmp_path: Path) -> None:
    archive = tmp_path / "a.zip"
    archive.write_bytes(b"content")
    pins = tmp_path / "checksums.json"
    verify_or_pin_checksum(archive, "demo", pins)

    archive.write_bytes(b"tampered")
    with pytest.raises(ChecksumMismatchError, match="pinned"):
        verify_or_pin_checksum(archive, "demo", pins)


def test_downloads_over_allowed_scheme_and_pins(settings: MLSettings, local_server: str) -> None:
    source = dataclasses.replace(PHIUSIIL, download_url=local_server)
    archive, checksum = ensure_archive(source, settings, allowed_schemes=("http",))

    assert archive.exists()
    assert checksum == sha256_of(archive)
    assert json.loads(settings.checksums_path.read_text())[PHIUSIIL.key] == checksum


def test_plain_http_is_refused_by_default(settings: MLSettings, local_server: str) -> None:
    source = dataclasses.replace(PHIUSIIL, download_url=local_server)
    with pytest.raises(ValueError, match="Refusing"):
        ensure_archive(source, settings)
    assert not (settings.raw_dir / f"{PHIUSIIL.key}.zip").exists()


def test_existing_archive_is_verified_not_redownloaded(settings_with_archive: MLSettings) -> None:
    # No network is reachable for this source URL; success proves the local file was used.
    source = dataclasses.replace(PHIUSIIL, download_url="https://invalid.invalid/none.zip")
    archive, _ = ensure_archive(source, settings_with_archive)
    assert archive.exists()
