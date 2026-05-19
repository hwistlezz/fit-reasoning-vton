import argparse
import sys
from pathlib import Path
from typing import List, Optional


README_CANDIDATES = [
    "README.md",
    "readme.md",
]

INFERENCE_CANDIDATES = [
    "inference.py",
    "infer.py",
    "demo.py",
    "app.py",
    "test.py",
    "gradio_demo/app.py",
    "src/inference.py",
]

ENVIRONMENT_CANDIDATES = [
    "requirements.txt",
    "environment.yml",
    "environment.yaml",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="외부 IDM-VTON 저장소의 기본 구조를 확인합니다."
    )
    parser.add_argument(
        "--idm-vton-root",
        default="../IDM-VTON",
        help="외부 IDM-VTON 저장소 경로입니다. 기본값은 ../IDM-VTON 입니다.",
    )
    return parser.parse_args()


def find_existing_file(root: Path, candidates: List[str]) -> Optional[Path]:
    for relative_path in candidates:
        file_path = root / relative_path
        if file_path.is_file():
            return file_path
    return None


def main() -> int:
    args = parse_args()
    idm_vton_root = Path(args.idm_vton_root).expanduser()

    print(f"확인 대상 IDM-VTON 경로: {idm_vton_root}")

    has_error = False
    if idm_vton_root.exists() and idm_vton_root.is_dir():
        print("경로 확인: 성공 - IDM-VTON 디렉터리가 존재합니다.")
    else:
        print("경로 확인: 실패 - IDM-VTON 디렉터리를 찾을 수 없습니다.")
        has_error = True

    readme_file = find_existing_file(idm_vton_root, README_CANDIDATES)
    if readme_file:
        print(f"README 확인: 성공 - {readme_file.relative_to(idm_vton_root)}")
    else:
        print("README 확인: 실패 - README.md 파일을 찾을 수 없습니다.")
        has_error = True

    inference_file = find_existing_file(idm_vton_root, INFERENCE_CANDIDATES)
    if inference_file:
        print(f"inference 후보 확인: 성공 - {inference_file.relative_to(idm_vton_root)}")
    else:
        print("inference 후보 확인: 주의 - 일반적인 inference/demo 파일 후보를 찾지 못했습니다.")
        print("확인한 후보:", ", ".join(INFERENCE_CANDIDATES))
        has_error = True

    environment_file = find_existing_file(idm_vton_root, ENVIRONMENT_CANDIDATES)
    if environment_file:
        print(f"환경 파일 후보 확인: 성공 - {environment_file.relative_to(idm_vton_root)}")
    else:
        print("환경 파일 후보 확인: 주의 - requirements, environment, pyproject 등 후보를 찾지 못했습니다.")
        print("확인한 후보:", ", ".join(ENVIRONMENT_CANDIDATES))
        has_error = True

    if has_error:
        print("검증 결과: 실패 - 외부 IDM-VTON 경로 또는 기본 파일 구성을 확인하세요.")
        return 1

    print("검증 결과: 성공 - 외부 IDM-VTON 저장소의 기본 구조가 확인되었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
