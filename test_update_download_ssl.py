from pathlib import Path

import update_manager
import update_system


class _FakeResponse:
    headers = {"content-length": "4"}

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size=8192):
        yield b"data"


def test_update_system_downloader_respects_verify_flag(tmp_path, monkeypatch):
    captured = {}

    def fake_get(url, stream, timeout, verify):
        captured["verify"] = verify
        return _FakeResponse()

    monkeypatch.setattr(update_system.requests, "get", fake_get)
    downloader = update_system.UpdateDownloader({}, str(tmp_path), verify=False)
    downloader.download_file("https://example.com/update.zip", str(Path(tmp_path) / "update.zip"))

    assert captured["verify"] is False


def test_update_manager_downloader_respects_verify_flag(tmp_path, monkeypatch):
    captured = {}

    def fake_get(url, stream, timeout, verify):
        captured["verify"] = verify
        return _FakeResponse()

    monkeypatch.setattr(update_manager.requests, "get", fake_get)
    downloader = update_manager.UpdateDownloader("https://example.com/update.zip", "update.zip", verify=False)
    downloader.run()

    assert captured["verify"] is False


def test_update_system_downloader_creates_nested_patch_dirs(tmp_path, monkeypatch):
    def fake_get(url, stream, timeout, verify):
        return _FakeResponse()

    monkeypatch.setattr(update_system.requests, "get", fake_get)
    nested_path = Path(tmp_path) / "patches" / "core" / "update.zip"
    downloader = update_system.UpdateDownloader({}, str(tmp_path), verify=False)

    downloader.download_file("https://example.com/update.zip", str(nested_path))

    assert nested_path.exists()
