import json
from pathlib import Path

import update_system
from build_incremental_update import build_patch_files


class _FakeResponse:
    headers = {"content-length": "4"}

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size=8192):
        yield b"data"


def test_update_downloader_downloads_incremental_patch_payloads(tmp_path, monkeypatch):
    requested = []

    def fake_get(url, stream, timeout, verify):
        requested.append(url)
        return _FakeResponse()

    monkeypatch.setattr(update_system.requests, "get", fake_get)

    update_info = {
        "patch_files": [
            {
                "name": "patches/core/update.bin",
                "url": "https://example.com/patches/core/update.bin",
                "target": "core/update.bin",
                "action": "replace",
            },
            {
                "target": "obsolete.txt",
                "action": "delete",
            },
        ]
    }

    downloader = update_system.UpdateDownloader(update_info, str(tmp_path), verify=False)
    downloader.download_patches(update_info["patch_files"])

    assert requested == ["https://example.com/patches/core/update.bin"]
    assert (tmp_path / "patches" / "core" / "update.bin").exists()
    assert not (tmp_path / "obsolete.txt").exists()


def test_update_installer_generates_incremental_patch_script(tmp_path, monkeypatch):
    update_dir = tmp_path / "updates"
    app_dir = tmp_path / "app"
    update_dir.mkdir()
    app_dir.mkdir()
    payload = update_dir / "patches" / "core" / "module.bin"
    payload.parent.mkdir(parents=True)
    payload.write_bytes(b"data")

    captured = {}

    def fake_popen(cmd, creationflags=None):
        captured["cmd"] = cmd
        captured["creationflags"] = creationflags
        return object()

    monkeypatch.setattr(update_system.subprocess, "Popen", fake_popen)

    installer = update_system.UpdateInstaller(str(update_dir), str(app_dir))
    success = installer.install_patches(
        [
            {
                "name": "patches/core/module.bin",
                "target": "core/module.bin",
                "action": "replace",
            },
            {
                "target": "old/unused.bin",
                "action": "delete",
            },
        ]
    )

    assert success is True
    script_path = Path(captured["cmd"][2])
    script_text = script_path.read_text(encoding="utf-8")
    assert "copy /y" in script_text
    assert "core\\module.bin" in script_text or "core/module.bin" in script_text
    assert "old\\unused.bin" in script_text or "old/unused.bin" in script_text


def test_update_installer_launches_downloaded_installer_package(tmp_path, monkeypatch):
    app_dir = tmp_path / "app"
    app_dir.mkdir()
    installer_file = tmp_path / "CADToolkit_Setup_v3.8.3.exe"
    installer_file.write_bytes(b"fake-installer")

    captured = {}

    def fake_popen(cmd, creationflags=None):
        captured["cmd"] = cmd
        captured["creationflags"] = creationflags
        return object()

    monkeypatch.setattr(update_system.subprocess, "Popen", fake_popen)

    installer = update_system.UpdateInstaller(str(tmp_path), str(app_dir))
    success = installer.install_full_package(str(installer_file))

    assert success is True
    script_path = Path(captured["cmd"][2])
    script_text = script_path.read_text(encoding="utf-8")
    assert 'start ""' in script_text
    assert installer_file.name in script_text
    assert "xcopy" not in script_text


def test_build_incremental_update_generates_patch_manifest(tmp_path):
    source = tmp_path / "module.py"
    source.write_text("print('hello')\n", encoding="utf-8")
    output_dir = tmp_path / "updates" / "3.8.2"

    manifest = build_patch_files(
        "3.8.2",
        "https://example.com/updates/3.8.2",
        output_dir,
        [f"{source}=core/module.py"],
    )

    assert manifest["version"] == "3.8.2"
    assert manifest["patch_files"][0]["name"] == "core/module.py"
    assert manifest["patch_files"][0]["target"] == "core/module.py"
    assert manifest["patch_files"][0]["url"] == "https://example.com/updates/3.8.2/core/module.py"
    assert (output_dir / "core" / "module.py").exists()
