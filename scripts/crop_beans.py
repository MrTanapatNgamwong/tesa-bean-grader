"""
crop_beans.py — ตัดเมล็ดกาแฟตามกรอบ label ออกมาเป็นภาพเดี่ยว (เฉพาะ 7 คลาสของโจทย์)

อินพุต : dataset แบบ YOLO detection (data.yaml + train/valid/test + images/labels)
เอาต์พุต: dataset แบบ classification สำหรับ YOLO26n-cls
          DST/train/<คลาส>/*.jpg · DST/val/<คลาส>/*.jpg · DST/test/<คลาส>/*.jpg

วิธีรัน (ที่ C:\\tesa-pi ใน venv):
    python scripts\\crop_beans.py                                   # ค่าเดิม: ROBUSTA → beans-cls
    python scripts\\crop_beans.py --preset nia --src datasets/coffee-defect-nia --dst datasets/beans-cls-nia --prefix nia
"""
import argparse
from pathlib import Path

import cv2
import yaml

# ชื่อคลาสใน dataset → ชื่อโฟลเดอร์ของเรา (คลาสที่ไม่อยู่ในนี้จะถูกข้าม)
PRESETS = {
    "robusta": {  # ROBUSTA DATASET (No digkit3)
        "good": "good", "shell": "shell", "full-black": "full_black", "husk": "husk",
        "broken-chipped-cut": "broken", "parchment": "parchment", "immature": "immature",
    },
    "nia": {      # coffee-bean-defect (niacubilla) · ข้าม foreign / infested / sour
        "green": "good", "black": "full_black", "broken": "broken",
        "husk": "husk", "fraghusk": "husk", "immature": "immature",
    },
    "cfe":{       # OPTIMIZED GREEN CFE BEANS · cherry = ผลแห้ง/เปลือกแห้ง → husk
        "normal": "good", "cherry": "husk", "black": "full_black", "broken": "broken",
    },
    "tss": {      # testsssss (rt-pee) · ไม่มี husk
        "normal": "good", "black": "full_black", "broken": "broken",
        "immature": "immature", "parchment": "parchment", "shell": "shell",
    },
}
SPLITS = {"train": "train", "valid": "val", "test": "test"}  # ชื่อโฟลเดอร์ต้นทาง → ปลายทาง


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="datasets/robusta-digkit3", help="โฟลเดอร์ dataset ต้นทาง")
    ap.add_argument("--dst", default="datasets/beans-cls", help="โฟลเดอร์ปลายทาง")
    ap.add_argument("--preset", default="robusta", choices=PRESETS, help="ตารางแปลงชื่อคลาส")
    ap.add_argument("--prefix", default="", help="คำนำหน้าชื่อไฟล์ กันชื่อชนเวลารวมหลาย dataset")
    ap.add_argument("--pad", type=float, default=0.10, help="เผื่อขอบรอบกรอบ (สัดส่วน)")
    ap.add_argument("--min-size", type=int, default=16, help="ข้ามกรอบเล็กกว่านี้ (พิกเซล)")
    ap.add_argument("--skip-edge", action="store_true", help="ข้ามกรอบที่ชิดขอบภาพ (เมล็ดถูกตัดไม่เต็มเม็ด)")
    args = ap.parse_args()

    src, dst, class_map = Path(args.src), Path(args.dst), PRESETS[args.preset]
    names = yaml.safe_load(open(src / "data.yaml", encoding="utf-8"))["names"]
    if isinstance(names, dict):  # บาง dataset เก็บ names เป็น {0: 'a', ...}
        names = [names[i] for i in sorted(names)]
    prefix = f"{args.prefix}_" if args.prefix else ""
    total = {}

    for src_split, dst_split in SPLITS.items():
        label_dir = src / src_split / "labels"
        if not label_dir.exists():
            continue
        for label_file in sorted(label_dir.glob("*.txt")):
            images = list((src / src_split / "images").glob(label_file.stem + ".*"))
            if not images:
                continue
            img = cv2.imread(str(images[0]))
            h, w = img.shape[:2]
            for i, line in enumerate(label_file.read_text().splitlines()):
                if not line.strip():
                    continue
                vals = list(map(float, line.split()))
                cls_id, coords = vals[0], vals[1:]
                if len(coords) == 4:          # กรอบปกติ: x_กลาง y_กลาง กว้าง สูง
                    x, y, bw, bh = coords
                else:                         # polygon: x1 y1 x2 y2 ... → กรอบที่ครอบทุกจุด
                    xs, ys = coords[0::2], coords[1::2]
                    x, y = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
                    bw, bh = max(xs) - min(xs), max(ys) - min(ys)
                if args.skip_edge and (x - bw / 2 < 0.005 or y - bh / 2 < 0.005 or x + bw / 2 > 0.995 or y + bh / 2 > 0.995):
                    continue
                cls = class_map.get(names[int(cls_id)])
                if cls is None:
                    continue
                bw_px, bh_px = bw * w * (1 + args.pad), bh * h * (1 + args.pad)
                x1, y1 = max(0, int(x * w - bw_px / 2)), max(0, int(y * h - bh_px / 2))
                x2, y2 = min(w, int(x * w + bw_px / 2)), min(h, int(y * h + bh_px / 2))
                if min(x2 - x1, y2 - y1) < args.min_size:
                    continue
                out_dir = dst / dst_split / cls
                out_dir.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(out_dir / f"{prefix}{label_file.stem}_{i}.jpg"), img[y1:y2, x1:x2])
                total[(dst_split, cls)] = total.get((dst_split, cls), 0) + 1

    classes = sorted({c for c in class_map.values()})
    print(f"{'class':<12}" + "".join(f"{s:>8}" for s in SPLITS.values()))
    for cls in classes:
        print(f"{cls:<12}" + "".join(f"{total.get((s, cls), 0):>8}" for s in SPLITS.values()))
    print("saved to", dst.resolve())


if __name__ == "__main__":
    main()
