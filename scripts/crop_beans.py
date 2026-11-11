"""
crop_beans.py — ตัดเมล็ดกาแฟตามกรอบ label ออกมาเป็นภาพเดี่ยว (เฉพาะ 7 คลาสของโจทย์)

อินพุต : dataset แบบ YOLO detection (มี data.yaml, train/valid/test, images/labels)
เอาต์พุต: dataset แบบ classification ที่ Ultralytics ใช้เทรน YOLO26n-cls ได้ทันที
          DST/train/<คลาส>/*.jpg · DST/val/<คลาส>/*.jpg · DST/test/<คลาส>/*.jpg

วิธีรัน (ที่ C:\\tesa-pi ใน venv):
    python scripts\\crop_beans.py
"""
from pathlib import Path
import cv2
import yaml

# ===== ตั้งค่า (วันจริงแก้แค่ส่วนนี้) =====
SRC = Path("datasets/robusta-digkit3")   # dataset ต้นทาง
DST = Path("datasets/beans-cls")         # โฟลเดอร์ปลายทาง
PAD = 0.10                               # เผื่อขอบรอบกรอบ 10% กันตัดเมล็ดแหว่ง
MIN_SIZE = 16                            # ข้ามกรอบที่เล็กกว่านี้ (พิกเซล) เพราะน่าจะเป็นเศษ

# ชื่อคลาสใน dataset → ชื่อโฟลเดอร์ของเรา (คลาสที่ไม่อยู่ในนี้จะถูกข้าม)
CLASS_MAP = {
    "good": "good",
    "shell": "shell",
    "full-black": "full_black",
    "husk": "husk",
    "broken-chipped-cut": "broken",
    "parchment": "parchment",
    "immature": "immature",
}

# Ultralytics classification ใช้ชื่อโฟลเดอร์ train / val / test
SPLITS = {"train": "train", "valid": "val", "test": "test"}


def main():
    names = yaml.safe_load(open(SRC / "data.yaml", encoding="utf-8"))["names"]
    total = {}

    for src_split, dst_split in SPLITS.items():
        for label_file in sorted((SRC / src_split / "labels").glob("*.txt")):
            # หาไฟล์ภาพคู่กับ label (ชื่อเดียวกัน นามสกุลอาจต่างกัน)
            images = list((SRC / src_split / "images").glob(label_file.stem + ".*"))
            if not images:
                continue
            img = cv2.imread(str(images[0]))
            h, w = img.shape[:2]

            for i, line in enumerate(label_file.read_text().splitlines()):
                if not line.strip():
                    continue
                cls_id, x, y, bw, bh = map(float, line.split()[:5])
                cls = CLASS_MAP.get(names[int(cls_id)])
                if cls is None:
                    continue  # ไม่ใช่ 7 คลาสของโจทย์

                # YOLO เก็บกรอบเป็น (กึ่งกลาง x, y, กว้าง, สูง) แบบสัดส่วน 0–1 → แปลงเป็นพิกเซล
                bw_px, bh_px = bw * w * (1 + PAD), bh * h * (1 + PAD)
                x1 = max(0, int(x * w - bw_px / 2))
                y1 = max(0, int(y * h - bh_px / 2))
                x2 = min(w, int(x * w + bw_px / 2))
                y2 = min(h, int(y * h + bh_px / 2))
                if min(x2 - x1, y2 - y1) < MIN_SIZE:
                    continue

                out_dir = DST / dst_split / cls
                out_dir.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(out_dir / f"{label_file.stem}_{i}.jpg"), img[y1:y2, x1:x2])
                total[(dst_split, cls)] = total.get((dst_split, cls), 0) + 1

    # สรุปจำนวนเมล็ดที่ตัดได้
    print(f"{'class':<12}" + "".join(f"{s:>8}" for s in SPLITS.values()))
    for cls in CLASS_MAP.values():
        print(f"{cls:<12}" + "".join(f"{total.get((s, cls), 0):>8}" for s in SPLITS.values()))
    print("saved to", DST.resolve())


if __name__ == "__main__":
    main()
