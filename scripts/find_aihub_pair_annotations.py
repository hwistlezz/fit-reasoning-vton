from pathlib import Path
import json
import argparse

EXCLUDE_DIR_NAMES = {"ddd", "_ignore_ddd", "__MACOSX"}

def is_excluded(path: Path) -> bool:
    return any(part in EXCLUDE_DIR_NAMES for part in path.parts)

def safe_load_json(path: Path):
    for enc in ("utf-8-sig", "utf-8", "cp949"):
        try:
            with path.open("r", encoding=enc) as f:
                return json.load(f)
        except Exception:
            pass
    return None

def has_pair_dict(obj):
    if isinstance(obj, dict):
        if all(k in obj for k in ("from", "to", "result")):
            return True

        for v in obj.values():
            if has_pair_dict(v):
                return True

    if isinstance(obj, list):
        for x in obj:
            if has_pair_dict(x):
                return True

    return False

def count_pair_dicts(obj):
    count = 0

    if isinstance(obj, dict):
        if all(k in obj for k in ("from", "to", "result")):
            count += 1

        for v in obj.values():
            count += count_pair_dicts(v)

    elif isinstance(obj, list):
        for x in obj:
            count += count_pair_dicts(x)

    return count

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    root = Path(args.root)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    total_pair_rows = 0

    for p in root.rglob("*.json"):
        if is_excluded(p):
            continue

        obj = safe_load_json(p)
        if obj is None:
            continue

        c = count_pair_dicts(obj)
        if c > 0:
            rows.append((str(p), c))
            total_pair_rows += c

    with out.open("w", encoding="utf-8-sig") as f:
        f.write("json_path,num_pair_rows\n")
        for path, count in rows:
            f.write(f'"{path}",{count}\n')

    print("[OK] pair annotation json files:", len(rows))
    print("[OK] total pair rows:", total_pair_rows)
    print("[OK] wrote:", out)

    print("\nSamples:")
    for path, count in rows[:20]:
        print(count, path)

if __name__ == "__main__":
    main()