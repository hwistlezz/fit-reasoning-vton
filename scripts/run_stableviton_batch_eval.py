import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path


REQUIRED_COLUMNS = {"case_id", "person_image", "cloth_image"}
OPTIONAL_COLUMNS = {"mode", "expected_note"}
VALID_MODES = {"paired", "unpaired"}
DEFAULT_MODE = "unpaired"


@dataclass(frozen=True)
class BatchCase:
    case_id: str
    person_image: str
    cloth_image: str
    mode: str
    expected_note: str


class BatchEvalError(Exception):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Dry-run preflight for PC3 StableVITON batch evaluation."
    )
    parser.add_argument(
        "--stableviton-root",
        required=True,
        help="External StableVITON repository path.",
    )
    parser.add_argument(
        "--pair-list",
        required=True,
        help="Batch pair CSV path.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        help="Ignored output root for generated batch outputs.",
    )
    parser.add_argument(
        "--mode",
        choices=sorted(VALID_MODES),
        default=DEFAULT_MODE,
        help=f"Default pair mode when the CSV row has no mode. Default: {DEFAULT_MODE}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate pair list and print the execution plan without running inference.",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="Validate only the first N cases.",
    )
    return parser.parse_args()


def print_status(status: str, label: str, detail: str = "") -> None:
    if detail:
        print(f"[{status}] {label}: {detail}")
    else:
        print(f"[{status}] {label}")


def validate_stableviton_root(path: Path) -> None:
    if not path.is_dir():
        raise BatchEvalError(f"StableVITON root does not exist: {path}")


def validate_pair_list_path(path: Path) -> None:
    if not path.is_file():
        raise BatchEvalError(f"Pair list CSV does not exist: {path}")


def validate_max_cases(max_cases: int | None) -> None:
    if max_cases is not None and max_cases < 1:
        raise BatchEvalError("--max-cases must be at least 1.")


def read_pair_list(path: Path, default_mode: str) -> list[BatchCase]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = sorted(REQUIRED_COLUMNS - fieldnames)
        if missing_columns:
            raise BatchEvalError(
                "Pair list CSV is missing required column(s): " + ", ".join(missing_columns)
            )

        cases: list[BatchCase] = []
        seen_case_ids: set[str] = set()
        for row_number, row in enumerate(reader, start=2):
            case_id = (row.get("case_id") or "").strip()
            person_image = (row.get("person_image") or "").strip()
            cloth_image = (row.get("cloth_image") or "").strip()
            mode = (row.get("mode") or default_mode).strip()
            expected_note = (row.get("expected_note") or "").strip()

            if not case_id:
                raise BatchEvalError(f"case_id is empty at CSV row {row_number}.")
            if case_id in seen_case_ids:
                raise BatchEvalError(f"Duplicate case_id found: {case_id}")
            if not person_image:
                raise BatchEvalError(f"person_image is empty for case_id={case_id}.")
            if not cloth_image:
                raise BatchEvalError(f"cloth_image is empty for case_id={case_id}.")
            if mode not in VALID_MODES:
                raise BatchEvalError(
                    f"Invalid mode for case_id={case_id}: {mode}. Expected paired or unpaired."
                )

            seen_case_ids.add(case_id)
            cases.append(
                BatchCase(
                    case_id=case_id,
                    person_image=person_image,
                    cloth_image=cloth_image,
                    mode=mode,
                    expected_note=expected_note,
                )
            )

    if not cases:
        raise BatchEvalError(f"Pair list CSV has no cases: {path}")
    return cases


def select_cases(cases: list[BatchCase], max_cases: int | None) -> list[BatchCase]:
    if max_cases is None:
        return cases
    return cases[:max_cases]


def format_bool(value: bool) -> str:
    return "true" if value else "false"


def print_plan(
    *,
    stableviton_root: Path,
    pair_list: Path,
    output_root: Path,
    all_cases: list[BatchCase],
    selected_cases: list[BatchCase],
    dry_run: bool,
) -> None:
    print("StableVITON batch evaluation preflight:")
    print_status("OK", "StableVITON root", str(stableviton_root))
    print_status("OK", "pair list", str(pair_list))
    print_status("OK", "output root", str(output_root))
    print_status("OK", "total cases", str(len(all_cases)))
    print_status("OK", "selected cases", str(len(selected_cases)))
    print_status("OK", "dry-run", format_bool(dry_run))

    print()
    print("Cases:")
    for case in selected_cases:
        expected_output_dir = output_root / case.case_id
        note_suffix = f" | note: {case.expected_note}" if case.expected_note else ""
        print(
            f"- {case.case_id}: {case.person_image} -> {case.cloth_image} "
            f"({case.mode}){note_suffix}"
        )
        print(f"  expected output directory: {expected_output_dir}")


def main() -> int:
    args = parse_args()
    stableviton_root = Path(args.stableviton_root).expanduser()
    pair_list = Path(args.pair_list).expanduser()
    output_root = Path(args.output_root).expanduser()

    try:
        validate_max_cases(args.max_cases)
        validate_stableviton_root(stableviton_root)
        validate_pair_list_path(pair_list)
        cases = read_pair_list(pair_list, args.mode)
        selected_cases = select_cases(cases, args.max_cases)
    except BatchEvalError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    print_plan(
        stableviton_root=stableviton_root,
        pair_list=pair_list,
        output_root=output_root,
        all_cases=cases,
        selected_cases=selected_cases,
        dry_run=args.dry_run,
    )

    if not args.dry_run:
        print()
        print("Actual batch inference is not implemented yet. Use --dry-run for preflight.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
