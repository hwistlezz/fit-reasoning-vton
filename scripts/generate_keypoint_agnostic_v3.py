from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np


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
    ap.add_argument("--dilate", type=int, default=55)
    ap.add_argument("--close-kernel", type=int, default=31)
    ap.add_argument("--torso-expand-x", type=float, default=0.48)
    ap.add_argument("--hip-expand-x", type=float, default=0.38)
    ap.add_argument("--top-margin", type=float, default=0.12)
    ap.add_argument("--bottom-margin", type=float, default=0.16)
    ap.add_argument("--arm-scale", type=float, default=0.16)
    ap.add_argument("--arm-circle-scale", type=float, default=0.20)
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
    return float(v[0]), float(v[1])


def fill_poly(mask, pts):
    pts = np.array([[int(round(x)), int(round(y))] for x, y in pts], dtype=np.int32)
    cv2.fillPoly(mask, [pts], 255)


def draw_capsule(mask, a, b, radius):
    if a is None or b is None:
        return
    axy = (int(round(a[0])), int(round(a[1])))
    bxy = (int(round(b[0])), int(round(b[1])))
    cv2.line(mask, axy, bxy, 255, radius * 2)
    cv2.circle(mask, axy, radius, 255, -1)
    cv2.circle(mask, bxy, radius, 255, -1)


def blend_point(a, b, t):
    return (a[0] * (1 - t) + b[0] * t, a[1] * (1 - t) + b[1] * t)


def make_mask(image_shape, kps, include_arms=True, dilate=55, close_kernel=31,
              torso_expand_x=0.48, hip_expand_x=0.38,
              top_margin=0.12, bottom_margin=0.16,
              arm_scale=0.16, arm_circle_scale=0.20):
    h, w = image_shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)

    ls = xy(kps, "left_shoulder")
    rs = xy(kps, "right_shoulder")
    lh = xy(kps, "left_hip")
    rh = xy(kps, "right_hip")
    neck = xy(kps, "neck")

    if not all([ls, rs, lh, rh]):
        return mask

    shoulder_width = max(20.0, np.linalg.norm(np.array(ls) - np.array(rs)))
    shoulder_y = (ls[1] + rs[1]) / 2.0
    hip_y = (lh[1] + rh[1]) / 2.0
    torso_h = max(35.0, hip_y - shoulder_y)

    top_y = shoulder_y - torso_h * top_margin
    if neck is not None:
        top_y = max(top_y, neck[1] - torso_h * 0.05)
    top_y = max(0.0, top_y)

    bottom_y = min(h - 1.0, hip_y + torso_h * bottom_margin)

    sx = shoulder_width * torso_expand_x
    hx = shoulder_width * hip_expand_x

    left_top = (max(0.0, ls[0] - sx), top_y)
    right_top = (min(w - 1.0, rs[0] + sx), top_y)
    right_mid = (min(w - 1.0, rs[0] + sx * 0.92), shoulder_y + torso_h * 0.30)
    right_bottom = (min(w - 1.0, rh[0] + hx), bottom_y)
    left_bottom = (max(0.0, lh[0] - hx), bottom_y)
    left_mid = (max(0.0, ls[0] - sx * 0.92), shoulder_y + torso_h * 0.30)

    torso_pts = [left_top, right_top, right_mid, right_bottom, left_bottom, left_mid]
    fill_poly(mask, torso_pts)

    # chest cap
    chest_top_y = max(0.0, top_y - torso_h * 0.04)
    chest_pts = [
        (max(0.0, ls[0] - sx * 0.55), chest_top_y),
        (min(w - 1.0, rs[0] + sx * 0.55), chest_top_y),
        (min(w - 1.0, rs[0] + sx * 0.42), shoulder_y + torso_h * 0.12),
        (max(0.0, ls[0] - sx * 0.42), shoulder_y + torso_h * 0.12),
    ]
    fill_poly(mask, chest_pts)

    if include_arms:
        le = xy(kps, "left_elbow")
        lw = xy(kps, "left_wrist")
        re = xy(kps, "right_elbow")
        rw = xy(kps, "right_wrist")

        arm_r = int(max(16, shoulder_width * arm_scale))
        joint_r = int(max(18, shoulder_width * arm_circle_scale))

        if le is not None:
            draw_capsule(mask, ls, le, arm_r)
            cv2.circle(mask, (int(round(le[0])), int(round(le[1]))), joint_r, 255, -1)
        if lw is not None and le is not None:
            draw_capsule(mask, le, lw, arm_r)
            cv2.circle(mask, (int(round(lw[0])), int(round(lw[1]))), joint_r, 255, -1)

        if re is not None:
            draw_capsule(mask, rs, re, arm_r)
            cv2.circle(mask, (int(round(re[0])), int(round(re[1]))), joint_r, 255, -1)
        if rw is not None and re is not None:
            draw_capsule(mask, re, rw, arm_r)
            cv2.circle(mask, (int(round(rw[0])), int(round(rw[1]))), joint_r, 255, -1)

        # blend shoulder to upper chest for smoother arm roots
        left_root = blend_point(ls, lh, 0.18)
        right_root = blend_point(rs, rh, 0.18)
        fill_poly(mask, [left_top, (ls[0], shoulder_y), left_root, left_mid])
        fill_poly(mask, [(rs[0], shoulder_y), right_top, right_mid, right_root])

    if close_kernel > 1:
        k = np.ones((close_kernel, close_kernel), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k)

    if dilate > 0:
        k2 = np.ones((dilate, dilate), np.uint8)
        mask = cv2.dilate(mask, k2, iterations=1)

    # clip mask not too low
    lower_clip = int(min(h - 1, hip_y + torso_h * 0.40))
    mask[lower_clip:, :] = 0

    return mask


def mask_filename(person_name: str):
    return f"{Path(person_name).stem}_mask.png"


def process_one(data_root: Path, person_name: str, gray_value: int, include_arms: bool,
                dilate: int, close_kernel: int, torso_expand_x: float, hip_expand_x: float,
                top_margin: float, bottom_margin: float, arm_scale: float, arm_circle_scale: float):
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
    mask = make_mask(
        image.shape,
        kps,
        include_arms=include_arms,
        dilate=dilate,
        close_kernel=close_kernel,
        torso_expand_x=torso_expand_x,
        hip_expand_x=hip_expand_x,
        top_margin=top_margin,
        bottom_margin=bottom_margin,
        arm_scale=arm_scale,
        arm_circle_scale=arm_circle_scale,
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
            args.close_kernel,
            args.torso_expand_x,
            args.hip_expand_x,
            args.top_margin,
            args.bottom_margin,
            args.arm_scale,
            args.arm_circle_scale,
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