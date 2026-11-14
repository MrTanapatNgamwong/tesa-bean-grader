"""
phone_to_cls.py — แปลง phone_crops (ภาพเมล็ดที่ตัดแล้ว + labels.csv) เป็น dataset classification

อินพุต : phone_crops/raw/<โฟลเดอร์ต้นทาง>/<crop_id>.jpg + phone_crops/labels.csv
         labels.csv: crop_id, src_label, draft, conf, final, by
         คลาสที่ใช้ = final (ถ้ามี) ไม่งั้นใช้ draft · ข้าม reject และคลาสที่ไม่อยู่ใน 7 คลาส
เอาต์พุต: DST/all/<คลาส>/phone_<crop_id>.jpg
         (ใส่ใน RESPLIT ของ merge_cls.py ให้แบ่ง train/val/test ใหม่ตามภาพถ่ายต้นฉบับ)

วิธีรัน (ที่ C:\\tesa-pi ใน venv):
    python scripts\\phone_to_cls.py --src D:/tesa-bean-grader-main/datasets/phone_crops --dst datasets/beans-cls-phone
"""
import argparse
import csv
import shutil
from collections import Counter
from pathlib import Path

CLASSES = {"good", "shell", "full_black", "husk", "broken", "parchment", "immature"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="โฟลเดอร์ phone_crops")
    ap.add_argument("--dst", default="datasets/beans-cls-phone")
    ap.add_argument("--kind", default="raw", choices=["raw", "masked"], help="raw = มีพื้นไม้ (ตรงกับภาพจริง) · masked = ลบพื้นแล้ว")
    ap.add_argument("--skip", default="", help="คลาสที่ไม่เอา คั่นด้วย , เช่น husk")
    args = ap.parse_args()

    src, dst = Path(args.src), Path(args.dst)
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    if dst.exists():
        shutil.rmtree(dst)  # สร้างใหม่ทุกครั้ง กันไฟล์เก่าค้าง
    counts, missing = Counter(), 0
    with open(src / "labels.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cls = (row["final"] or row["draft"]).strip()
            if cls not in CLASSES or cls in skip:
                counts["(ข้าม) " + cls] += 1
                continue
            img = src / args.kind / row["src_label"] / f"{row['crop_id']}.jpg"
            if not img.exists():
                missing += 1
                continue
            out = dst / "all" / cls
            out.mkdir(parents=True, exist_ok=True)
            shutil.copy(img, out / f"phone_{row['crop_id']}.jpg")
            counts[cls] += 1
    for k, v in sorted(counts.items()):
        print(f"{k:<20}{v:>6}")
    if missing:
        print("ไม่พบไฟล์ภาพ:", missing)
    print("saved to", dst.resolve())


if __name__ == "__main__":
    main()
