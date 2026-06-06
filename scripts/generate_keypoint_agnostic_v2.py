from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np


GRAY_VALUE = 128


OPENPOSE = {
    "nose": 0,
    "neck": 1,
    "right_shoulder": 2,
    "right_elbow": 3,
    "right_wrist": 4,
    "left_shoulder": 5,
    "left_elbow": 6,
    "left_wrist": 7,
    "right_hip": 8,
    "right_knee": 9,
    "right_ankle": 10,
    "left_hip": 11,
    "left_knee": 12,
    "left_ankle": 13,
    "right_eye": 14,
    "left_eye": 15,
    "right_ear": 16,
    "left_ear": 17,
}


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--gray-value", type=int, default=128)
    ap.add_argument("--include-arms", action="store_true")
    ap.add_argument("--dilate", type=int, default=35)
    ap.add_argument("--top-margin", type=float, default=0.18)
    ap.add_argument("--bottom-margin", type=float, default=0.18)
    return ap.parse_args()


def read_pairs(data_root: Path):
    p = data_root / "test_pairs.txt"
    if not p.exists():
        raise FileNotFoundError(p)
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        parts = s.split()
        if len(parts) != 2:
            raise ValueError(f"bad pair line: {s}")
        rows.append((parts[0], parts[1]))
    return rows


def load_keypoints(path: Path):
    if not path.exists():
        return {}
    obj = json.loads(path.read_text(encoding="utf-8"))
    people = obj.get("people") or []
    if not people:
        return {}
    arr = people[0].get("pose_keypoints_2d") or []
    out = {}
    for name, idx in OPENPOSE.items():
        j = idx * 3
        if j + 2 < len(arr):
            x, y, c = float(arr[j]), float(arr[j + 1]), float(arr[j + 2])
            if x > 0 and y > 0 and c > 0.05:
                out[name] = (x, y, c)
    return out


def xy(kps, name):
    v = kps.get(name)
    if not v:
        return None
    return (float(v[0]), float(v[1]))


def draw_poly(mask, pts):
    pts = np.array([[int(x), int(y)] for x, y in pts], dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)


def add_limb(mask, a, b, radius):
    if a is None or b is None:
        return
    cv2.line(mask, (int(a[0]), int(a[1])), (int(b[0]), int(b[1])), 255, radius)


def make_upper_body_mask(image_shape, kps, include_arms=True, dilate=35, top_margin=0.18, bottom_margin=0.18):
    h, w = image_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    ls = xy(kps, "left_shoulder")
    rs = xy(kps, "right_shoulder")
    lh = xy(kps, "left_hip")
    rh = xy(kps, "right_hip")

    if not all([ls, rs, lh, rh]):
        return mask

    shoulder_width = max(20.0, abs(ls[0] - rs[0]))
    torso_height = max(30.0, ((lh[1] + rh[1]) / 2.0) - ((ls[1] + rs[1]) / 2.0))

    top_y = max(0, min(ls[1], rs[1]) - torso_height * top_margin)
    bottom_y = min(h - 1, max(lh[1], rh[1]) + torso_height * bottom_margin)

    expand_x = shoulder_width * 0.35

    left_top = (max(0, ls[0] - expand_x), top_y)
    right_top = (min(w - 1, rs[0] + expand_x), top_y)
    right_bottom = (min(w - 1, rh[0] + expand_x * 0.65), bottom_y)
    left_bottom = (max(0, lh[0] - expand_x * 0.65), bottom_y)

    draw_poly(mask, [left_top, right_top, right_bottom, left_bottom])

    if include_arms:
        le = xy(kps, "left_elbow")
        lw = xy(kps, "left_wrist")
        re = xy(kps, "right_elbow")
        rw = xy(kps, "right_wrist")
        radius = int(max(18, shoulder_width * 0.13))
        add_limb(mask, ls, le, radius)
        add_limb(mask, le, lw, radius)
        add_limb(mask, rs, re, radius)
        add_limb(mask, re, rw, radius)

    if dilate > 0:
        kernel = np.ones((dilate, dilate), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)

    return mask


def mask_filename(person_name: str):
    p = Path(person_name)
    return f"{p.stem}_mask.png"


def process_one(data_root: Path, person_name: str, gray_value: int, include_arms: bool, dilate: int, top_margin: float, bottom_margin: float):
    image_path = data_root / "test" / "image" / person_name
    kp_path = data_root / "test" / "openpose-json" / f"{Path(person_name).stem}_keypoints.json"

    if not image_path.exists():
        print("[WARN] missing image", image_path)
        return False
    if not kp_path.exists():
        print("[WARN] missing keypoints", kp_path)
        return False

    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        print("[WARN] failed image read", image_path)
        return False

    kps = load_keypoints(kp_path)
    mask = make_upper_body_mask(
        image.shape,
        kps,
        include_arms=include_arms,
        dilate=dilate,
        top_margin=top_margin,
        bottom_margin=bottom_margin,
    )

    if int(mask.sum()) <= 0:
        print("[WARN] empty mask", person_name)
        return False

    agnostic = image.copy()
    agnostic[mask > 0] = (gray_value, gray_value, gray_value)

    out_img = data_root / "test" / "agnostic-v3.2"
    out_mask = data_root / "test" / "agnostic-mask"
    out_img.mkdir(parents=True, exist_ok=True)
    out_mask.mkdir(parents=True, exist_ok=True)

    ok1 = cv2.imwrite(str(out_img / person_name), agnostic)
    ok2 = cv2.imwrite(str(out_mask / mask_filename(person_name)), mask)
    if not ok1 or not ok2:
        print("[WARN] failed write", person_name)
        return False

    print("[OK]", person_name)
    return True


def main():
    args = parse_args()
    data_root = Path(args.data_root)
    pairs = read_pairs(data_root)

    seen = set()
    ok = 0
    fail = 0

    for person_name, _cloth in pairs:
        if person_name in seen:
            continue
        seen.add(person_name)
        if process_one(
            data_root,
            person_name,
            args.gray_value,
            args.include_arms,
            args.dilate,
            args.top_margin,
            args.bottom_margin,
        ):
            ok += 1
        else:
            fail += 1

    print()
    print("Summary:")
    print("people=", len(seen))
    print("generated=", ok)
    print("failed=", fail)
    print("data_root=", data_root)
    return 0 if ok > 0 else 1


if __name__ == "__main__":
    sys.exit(main())