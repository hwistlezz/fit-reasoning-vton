import argparse
import sys
from pathlib import Path
from typing import Iterable, List, Optional


README_CANDIDATES = [
    "README.md",
    "readme.md",
]

EXECUTION_CANDIDATES = [
    "inference.py",
    "infer.py",
    "test.py",
    "train.py",
    "demo.py",
    "app.py",
    "scripts/inference.py",
    "src/inference.py",
]

ENVIRONMENT_CANDIDATES = [
    "requirements.txt",
    "environment.yml",
    "environment.yaml",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "configs",
    "config",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="외부 StableVITON 저장소의 기본 구조를 확인합니다."
    )
    parser.add_argument(
        "--stableviton-root",
        default="../StableVITON",
        help="외부 StableVITON 저장소 경로입니다. 기본값은 ../StableVITON 입니다.",
    )
    return parser.parse_args()


def find_existing_path(root: Path, candidates: Iterable[str]) -> Optional[Path]:
    for relative_path in candidates:
        candidate_path = root / relative_path
        if candidate_path.exists():
            return candidate_path
    return None


def find_any_top_level_python_file(root: Path) -> Optional[Path]:
    if not root.exists() or not root.is_dir():
        return None

    for candidate_path in sorted(root.glob("*.py")):
        if candidate_path.is_file():
            return candidate_path
    return None


def format_relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def print_candidates(label: str, candidates: List[str]) -> None:
    print(f"{label} 후보:", ", ".join(candidates))


def main() -> int:
    args = parse_args()
    stableviton_root = Path(args.stableviton_root).expanduser()

    print(f"확인 대상 StableVITON 경로: {stableviton_root}")

    has_error = False
    if stableviton_root.exists() and stableviton_root.is_dir():
        print("경로 확인: 성공 - StableVITON 디렉터리가 존재합니다.")
    else:
        print("경로 확인: 실패 - StableVITON 디렉터리를 찾을 수 없습니다.")
        has_error = True

    readme_file = find_existing_path(stableviton_root, README_CANDIDATES)
    if readme_file and readme_file.is_file():
        print(f"README 확인: 성공 - {format_relative(readme_file, stableviton_root)}")
    else:
        print("README 확인: 실패 - README.md 파일을 찾을 수 없습니다.")
        print_candidates("README", README_CANDIDATES)
        has_error = True

    execution_file = find_existing_path(stableviton_root, EXECUTION_CANDIDATES)
    if not execution_file:
        execution_file = find_any_top_level_python_file(stableviton_root)

    if execution_file:
        print(f"실행 파일 후보 확인: 성공 - {format_relative(execution_file, stableviton_root)}")
    else:
        print("실행 파일 후보 확인: 주의 - 일반적인 inference/test/train 파일 후보를 찾지 못했습니다.")
        print_candidates("실행 파일", EXECUTION_CANDIDATES)
        has_error = True

    environment_path = find_existing_path(stableviton_root, ENVIRONMENT_CANDIDATES)
    if environment_path:
        print(f"환경 파일 후보 확인: 성공 - {format_relative(environment_path, stableviton_root)}")
    else:
        print("환경 파일 후보 확인: 주의 - requirements, environment, configs 등 후보를 찾지 못했습니다.")
        print_candidates("환경 파일", ENVIRONMENT_CANDIDATES)
        has_error = True

    if has_error:
        print("검증 결과: 실패 - 외부 StableVITON 저장소의 기본 구조를 확인하지 못했습니다.")
        return 1

    print("검증 결과: 성공 - 외부 StableVITON 저장소의 기본 구조가 확인되었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
