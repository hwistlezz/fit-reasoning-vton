import argparse
import sys
from pathlib import Path


REQUIRED_FILES = [
    "app.py",
    "inference.py",
    "eval.py",
    "requirements.txt",
    "README.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="외부 CatVTON 저장소의 기본 파일 존재 여부를 확인합니다."
    )
    parser.add_argument(
        "--catvton-root",
        default="../CatVTON",
        help="외부 CatVTON 저장소 경로입니다. 기본값은 ../CatVTON 입니다.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    catvton_root = Path(args.catvton_root).expanduser()

    print(f"확인 대상 CatVTON 경로: {catvton_root}")

    has_error = False
    if catvton_root.exists() and catvton_root.is_dir():
        print("경로 확인: 성공 - CatVTON 디렉터리가 존재합니다.")
    else:
        print("경로 확인: 실패 - CatVTON 디렉터리를 찾을 수 없습니다.")
        has_error = True

    for relative_path in REQUIRED_FILES:
        file_path = catvton_root / relative_path
        if file_path.is_file():
            print(f"파일 확인: 성공 - {relative_path}")
        else:
            print(f"파일 확인: 실패 - {relative_path} 파일이 없습니다.")
            has_error = True

    if has_error:
        print("검증 결과: 실패 - CatVTON 외부 저장소 경로 또는 필수 파일을 확인하세요.")
        return 1

    print("검증 결과: 성공 - 외부 CatVTON 저장소의 기본 구조가 확인되었습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

