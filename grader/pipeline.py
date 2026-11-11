"""
pipeline.py — ภาพเมล็ดกาแฟ → ตัดเมล็ด → classify → นับ → เกรด → JSON

ขั้นตอน
  1. ตัดเมล็ดออกจากภาพด้วย OpenCV (threshold + contour)  * ใช้ได้ดีกับพื้นหลังสีอ่อนเรียบ
  2. classify ทีละเม็ดด้วยโมเดล NCNN (cls_v2)
  3. นับต่อคลาส และคำนวณเกรดด้วย grade.py
  4. บันทึก JSON (สิ่งที่ server ต้องการ) + ภาพที่วาดกรอบและชื่อคลาส

วิธีรัน (บน Pi ที่ ~/tesa ใน venv):
    python grader/pipeline.py full-test/ภาพ.jpg --lot TEST-001
    python grader/pipeline.py full-test/*.jpg --lot TEST-002      # หลายภาพ = ล็อตเดียว
"""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))  # ให้ import grade.py ที่อยู่โฟลเดอร์เดียวกันได้
from grade import grade, load_config, merge_counts  # noqa: E402

# ===== ตั้งค่า =====
MODEL = "cls_v2_ncnn_model"   # โฟลเดอร์โมเดล (ชื่อต้องลงท้าย _ncnn_model)
IMGSZ = 320                   # ต้องตรงกับตอนเทรน
MIN_AREA_FRAC = 0.001         # ก้อนที่เล็กกว่า 0.1% ของภาพ = เศษ/จุดรบกวน ข้ามไป
PAD = 0.10                    # เผื่อขอบรอบเมล็ดตอนตัด (เหมือน crop_beans.py)
OUT_DIR = Path("results")
DEVICE_ID = "tesa-pi"

COLORS = {  # สีกรอบต่อคลาส (BGR)
    "good": (60, 180, 75), "full_black": (40, 40, 40), "husk": (19, 69, 139),
    "shell": (200, 130, 0), "broken": (0, 0, 230), "parchment": (0, 200, 230),
    "immature": (180, 30, 145),
}


def find_beans(img):
    """คืนรายการกรอบ (x1, y1, x2, y2) ของเมล็ดแต่ละเม็ด"""
    h, w = img.shape[:2]
    gray = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (5, 5), 0)
    # Otsu เลือกค่า threshold ให้อัตโนมัติ · INV เพราะเมล็ดเข้มกว่าพื้นหลัง → เมล็ดเป็นสีขาวใน mask
    _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)   # ลบจุดเล็ก ๆ
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)  # อุดรูในเมล็ด
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        if cv2.contourArea(c) < MIN_AREA_FRAC * h * w:
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        px, py = int(bw * PAD / 2), int(bh * PAD / 2)
        boxes.append((max(0, x - px), max(0, y - py), min(w, x + bw + px), min(h, y + bh + py)))
    return boxes


def image_metadata(path, img):
    """metadata ของภาพที่ส่งให้ server"""
    meta = {
        "filename": path.name,
        "width": img.shape[1],
        "height": img.shape[0],
        "size_bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()[:16],  # ตัวระบุภาพแบบสั้น
        "file_modified": datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
        "captured_at": None,
    }
    try:  # เวลาถ่ายจาก EXIF ถ้ามี (ภาพจากกล้อง/มือถือ)
        exif = Image.open(path).getexif()
        dt = exif.get_ifd(0x8769).get(36867) or exif.get(306)  # DateTimeOriginal หรือ DateTime
        if dt:
            meta["captured_at"] = datetime.strptime(dt, "%Y:%m:%d %H:%M:%S").isoformat()
    except Exception:
        pass
    return meta


def process_image(model, path, out_dir):
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"เปิดภาพไม่ได้: {path}")
    t0 = time.perf_counter()

    boxes = find_beans(img)
    t1 = time.perf_counter()

    counts = {}
    labels = []
    if boxes:
        crops = [img[y1:y2, x1:x2] for x1, y1, x2, y2 in boxes]
        results = model.predict(crops, imgsz=IMGSZ, verbose=False)  # ส่งทุกเม็ดเป็นชุดเดียว
        for r in results:
            name = r.names[r.probs.top1]
            labels.append((name, float(r.probs.top1conf)))
            counts[name] = counts.get(name, 0) + 1
    t2 = time.perf_counter()

    # วาดกรอบ + ชื่อคลาสลงภาพ
    vis = img.copy()
    for (x1, y1, x2, y2), (name, conf) in zip(boxes, labels):
        color = COLORS.get(name, (255, 255, 255))
        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
        cv2.putText(vis, f"{name} {conf:.2f}", (x1, max(12, y1 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
    annotated = out_dir / f"{path.stem}_annotated.jpg"
    cv2.imwrite(str(annotated), vis)

    meta = image_metadata(path, img)
    meta.update({
        "beans_detected": len(boxes),
        "counts": counts,
        "timing_ms": {"segment": round((t1 - t0) * 1000, 1), "classify": round((t2 - t1) * 1000, 1)},
        "annotated_image": annotated.name,
    })
    return counts, meta


def main():
    ap = argparse.ArgumentParser(description="Bean grading pipeline")
    ap.add_argument("images", nargs="+", type=Path, help="ภาพหนึ่งภาพหรือหลายภาพของล็อตเดียวกัน")
    ap.add_argument("--lot", default=datetime.now().strftime("LOT-%Y%m%d-%H%M%S"))
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()

    from ultralytics import YOLO  # import ตรงนี้เพื่อให้ --help ทำงานเร็ว
    model = YOLO(args.model, task="classify")
    cfg = load_config()
    OUT_DIR.mkdir(exist_ok=True)

    t_start = time.perf_counter()
    all_counts, images_meta = [], []
    for path in args.images:
        counts, meta = process_image(model, path, OUT_DIR)
        all_counts.append(counts)
        images_meta.append(meta)
        print(f"{path.name}: {meta['beans_detected']} เม็ด {counts}  "
              f"(ตัด {meta['timing_ms']['segment']} ms · classify {meta['timing_ms']['classify']} ms)")

    result = {
        "lot_id": args.lot,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "device_id": DEVICE_ID,
        "model": Path(args.model).name,
        "image_count": len(images_meta),
        **grade(merge_counts(*all_counts), cfg),
        "images": images_meta,
        "processing_ms": round((time.perf_counter() - t_start) * 1000, 1),
    }

    out_json = OUT_DIR / f"{args.lot}.json"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nรวม {result['total_beans']} เม็ด · ดี {result['good_ratio']:.1%} · เสีย {result['defect_ratio']:.1%}")
    print(f"full defects/350g = {result['full_defects_per_350g']} → เกรด {result['grade']}")
    if result["warning"]:
        print("⚠", result["warning"])
    print(f"บันทึก {out_json} และภาพ *_annotated.jpg ใน {OUT_DIR}/")


if __name__ == "__main__":
    main()
