"""
增量更新包生成工具。

用法示例:
python build_incremental_update.py ^
  --version 3.8.2 ^
  --base-url https://raw.githubusercontent.com/bataa7/cad-toolkit/main/updates/3.8.2 ^
  --file dist/CAD工具包.exe=CAD工具包.exe ^
  --file notifications.json=notifications.json ^
  --update-version-json
"""

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path
from urllib.parse import quote


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_file_mapping(spec: str):
    if "=" in spec:
        source, target = spec.split("=", 1)
    else:
        source = spec
        target = Path(spec).name
    return Path(source), Path(target)


def build_patch_files(version: str, base_url: str, output_dir: Path, file_specs):
    patch_files = []
    output_dir.mkdir(parents=True, exist_ok=True)

    for spec in file_specs:
        source_path, target_path = parse_file_mapping(spec)
        if not source_path.exists():
            raise FileNotFoundError(f"源文件不存在: {source_path}")

        payload_path = output_dir / target_path
        payload_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, payload_path)

        relative_name = target_path.as_posix()
        patch_files.append(
            {
                "name": relative_name,
                "url": base_url.rstrip("/") + "/" + quote(relative_name, safe="/"),
                "hash": sha256_file(payload_path),
                "target": relative_name,
                "action": "replace",
            }
        )

    manifest = {
        "version": version,
        "patch_files": patch_files,
        "size": sum((output_dir / Path(item["name"])).stat().st_size for item in patch_files),
    }
    return manifest


def update_version_json(version_json_path: Path, manifest: dict):
    data = json.loads(version_json_path.read_text(encoding="utf-8"))
    data["version"] = manifest["version"]
    data["patch_files"] = manifest["patch_files"]
    data["size"] = manifest["size"]
    version_json_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="生成 CAD 工具包增量更新包")
    parser.add_argument("--version", required=True, help="版本号，例如 3.8.2")
    parser.add_argument("--base-url", required=True, help="补丁文件在线基础地址")
    parser.add_argument("--output-dir", default=None, help="补丁输出目录，默认 updates/<version>")
    parser.add_argument(
        "--file",
        action="append",
        required=True,
        help="补丁文件映射，格式 source_path 或 source_path=target_relative_path",
    )
    parser.add_argument(
        "--update-version-json",
        action="store_true",
        help="将生成的 patch_files 写回根目录 version.json",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else Path("updates") / args.version
    manifest = build_patch_files(args.version, args.base_url, output_dir, args.file)

    manifest_path = output_dir / "patch_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已生成补丁清单: {manifest_path}")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))

    if args.update_version_json:
        update_version_json(Path("version.json"), manifest)
        print("已更新 version.json 中的 patch_files")


if __name__ == "__main__":
    main()
