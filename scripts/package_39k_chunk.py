#!/usr/bin/env python
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_FINAL_PACKAGE_ROOT = r"C:\fit_transfer\final_packages"
REQUIRED_FOLDERS = (
    "image",
    "cloth",
    "worn",
    "fit",
    "openpose-json",
    "image-parse",
    "cloth-mask",
    "image-densepose",
    "agnostic-v3.2",
    "agnostic-mask",
)
REQUIRED_VALIDATION_FILES = (
    "metadata_chunk_final.csv",
    "manifest_chunk_final.jsonl",
    "validation_report.json",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_validation_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing validation report: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def assert_validation_passed(report: dict[str, Any], allow_failed: bool) -> None:
    failed_count = int(report.get("failed_count", 0))
    status = str(report.get("status", "")).lower()
    if allow_failed:
        return
    if failed_count != 0 or status not in {"passed", "ok"}:
        raise ValueError(
            "Validation did not pass. Use --allow-failed-validation only for "
            "debug packaging, never for transfer packages."
        )


def package_name_from_chunk(chunk_id: str, version: str) -> str:
    return f"aihub_39k_artifact_{chunk_id}_{version}"


def find_existing_parts(output_root: Path, package_name: str) -> list[Path]:
    return sorted(output_root.glob(f"{package_name}.7z.*")) + sorted(output_root.glob(f"{package_name}.7z"))


def make_filelist(
    artifact_root: Path,
    validation_dir: Path,
    output_root: Path,
    package_name: str,
    package_summary: Path,
) -> Path:
    filelist = output_root / f"{package_name}_filelist.txt"
    entries: list[Path] = []
    for folder in REQUIRED_FOLDERS:
        path = artifact_root / folder
        if not path.exists():
            raise FileNotFoundError(f"Missing required artifact folder: {path}")
        entries.append(path)
    for filename in REQUIRED_VALIDATION_FILES:
        path = validation_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing required validation file: {path}")
        entries.append(path)
    entries.append(package_summary)
    filelist.write_text(
        "\n".join(str(path) for path in entries) + "\n",
        encoding="utf-8",
    )
    return filelist


def build_7z_command(
    seven_zip: str,
    archive_base: Path,
    split_size: str,
    filelist: Path,
) -> list[str]:
    return [
        seven_zip,
        "a",
        "-t7z",
        f"-v{split_size}",
        str(archive_base),
        f"@{filelist}",
    ]


def write_checksums(output_root: Path, package_name: str) -> Path:
    parts = find_existing_parts(output_root, package_name)
    checksum_path = output_root / f"{package_name}.sha256.txt"
    lines = [f"{sha256_file(path)}  {path.name}" for path in parts if path.exists()]
    checksum_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return checksum_path


def write_transfer_readme(
    output_root: Path,
    package_name: str,
    dry_run: bool,
    seven_zip: str,
    split_size: str,
    http_port: int,
) -> Path:
    readme = output_root / f"{package_name}_transfer_readme.md"
    test_command = f'{seven_zip} t "{output_root / (package_name + ".7z.001")}"'
    http_command = f'python -m http.server {http_port} --directory "{output_root}"'
    readme.write_text(
        "\n".join(
            [
                f"# {package_name} Transfer Readme",
                "",
                f"Dry run: {dry_run}",
                f"Split size: {split_size}",
                "",
                "## Before Transfer",
                "- Confirm validation_report.json status is passed.",
                "- Confirm sha256 file exists and includes every split part.",
                "- Run the 7z test command on the first split part.",
                "",
                "## 7z Test Command",
                "```powershell",
                test_command,
                "```",
                "",
                "## HTTP Server Command",
                "```powershell",
                http_command,
                "```",
                "",
                "HTTP transfer is manual. This script only prepares the package.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return readme


def run_command(command: list[str]) -> None:
    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {completed.returncode}: {command}")


def package(args: argparse.Namespace) -> dict[str, Any]:
    artifact_root = Path(args.artifact_root)
    validation_dir = Path(args.validation_dir)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    chunk_id = args.chunk_id or artifact_root.name
    package_name = args.package_name or package_name_from_chunk(chunk_id, args.version)
    validation_report_path = validation_dir / "validation_report.json"
    validation_report = load_validation_report(validation_report_path)
    assert_validation_passed(validation_report, args.allow_failed_validation)

    package_summary_path = output_root / f"{package_name}_package_summary.json"
    archive_base = output_root / f"{package_name}.7z"
    checksum_path = output_root / f"{package_name}.sha256.txt"
    transfer_readme = output_root / f"{package_name}_transfer_readme.md"

    summary: dict[str, Any] = {
        "package_name": package_name,
        "chunk_id": chunk_id,
        "artifact_root": str(artifact_root),
        "validation_dir": str(validation_dir),
        "output_root": str(output_root),
        "required_folders": list(REQUIRED_FOLDERS),
        "required_validation_files": list(REQUIRED_VALIDATION_FILES),
        "validation_report": str(validation_report_path),
        "validation_status": validation_report.get("status"),
        "validation_failed_count": validation_report.get("failed_count"),
        "dry_run": args.dry_run,
    }
    package_summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    filelist = make_filelist(
        artifact_root,
        validation_dir,
        output_root,
        package_name,
        package_summary_path,
    )
    command = build_7z_command(args.seven_zip, archive_base, args.split_size, filelist)
    summary["filelist"] = str(filelist)
    summary["archive_base"] = str(archive_base)
    summary["7z_command"] = command
    summary["7z_test_command"] = [args.seven_zip, "t", str(output_root / f"{package_name}.7z.001")]
    summary["http_server_command"] = [
        "python",
        "-m",
        "http.server",
        str(args.http_port),
        "--directory",
        str(output_root),
    ]

    if args.dry_run:
        summary["created_parts"] = []
        summary["checksum_path"] = str(checksum_path)
    else:
        if shutil.which(args.seven_zip) is None and not Path(args.seven_zip).exists():
            raise FileNotFoundError(f"7z executable not found: {args.seven_zip}")
        run_command(command)
        checksum = write_checksums(output_root, package_name)
        summary["created_parts"] = [str(path) for path in find_existing_parts(output_root, package_name)]
        summary["checksum_path"] = str(checksum)

    readme = write_transfer_readme(
        output_root,
        package_name,
        args.dry_run,
        args.seven_zip,
        args.split_size,
        args.http_port,
    )
    summary["transfer_readme"] = str(readme)
    package_summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare or create a validated 39k artifact chunk package."
    )
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--validation-dir", required=True)
    parser.add_argument("--output-root", default=DEFAULT_FINAL_PACKAGE_ROOT)
    parser.add_argument("--chunk-id")
    parser.add_argument("--package-name")
    parser.add_argument("--version", default="v1")
    parser.add_argument("--split-size", default="10g")
    parser.add_argument("--seven-zip", default="7z")
    parser.add_argument("--http-port", type=int, default=8000)
    parser.add_argument(
        "--dry-run",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Default true. Use --no-dry-run to actually run 7z.",
    )
    parser.add_argument("--allow-failed-validation", action="store_true")
    return parser.parse_args()


def main() -> None:
    print(json.dumps(package(parse_args()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
