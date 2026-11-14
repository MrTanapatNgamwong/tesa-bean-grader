"""
detect.py — ภาพเมล็ดกาแฟ → ตัดเมล็ด → classify 7 คลาส → นับ → JSON + ภาพวาดกรอบ

หน้าที่ของ Pi คือ "ตรวจจับและนับ" เท่านั้น · การคิดเกรดทำที่ฝั่ง server

ขั้นตอน
  1. ตัดเมล็ดออกจากภาพด้วย OpenCV (threshold + contour)  * ใช้ได้ดีกับพื้นหลังสีอ่อนเรียบ เมล็ดไม่ติดกัน
  2. classify ทีละเม็ดด้วยโมเดล NCNN (cls_v5)
  3. นับจำนวนเมล็ดต่อคลาส (ครบ 7 คลาส คลาสที่ไม่เจอ = 0)
  4. บันทึก JSON + ภาพที่วาดกรอบและชื่อคลาส

วิธีรัน (บน Pi ที่ ~/tesa ใน venv):
    python detector/detect.py full-test/ภาพ.jpg --lot TEST-001
    python detector/detect.py full-test/*.jpg --lot TEST-002      # หลายภาพ = ล็อตเดียว
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

# ===== ตั้งค่า =====
MODEL = "cls_v5_ncnn_model"   # โฟลเดอร์โมเดล (ชื่อต้องลงท้าย _ncnn_model)
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


def process_image(model, class_names, path, out_dir):
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"เปิดภาพไม่ได้: {path}")
    t0 = time.perf_counter()

    boxes = find_beans(img)
    t1 = time.perf_counter()

    counts = {name: 0 for name in class_names}
    beans = []
    if boxes:
        crops = [img[y1:y2, x1:x2] for x1, y1, x2, y2 in boxes]
        results = model.predict(crops, imgsz=IMGSZ, verbose=False)  # ส่งทุกเม็ดเป็นชุดเดียว
        for box, r in zip(boxes, results):
            name = r.names[r.probs.top1]
            counts[name] += 1
            beans.append({"class": name, "conf": round(float(r.probs.top1conf), 3), "box": list(box)})
    t2 = time.perf_counter()

    # วาดกรอบ + ชื่อคลาสลงภาพ
    vis = img.copy()
    for b in beans:
        x1, y1, x2, y2 = b["box"]
        color = COLORS.get(b["class"], (255, 255, 255))
        cv2.rectangle(vis, (x1, y1), (x2, y2), color, 2)
        cv2.putText(vis, f"{b['class']} {b['conf']:.2f}", (x1, max(12, y1 - 4)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
    annotated = out_dir / f"{path.stem}_annotated.jpg"
    cv2.imwrite(str(annotated), vis)

    return {
        "filename": path.name,
        "beans_detected": len(beans),
        "counts": counts,
        "beans": beans,
        "timing_ms": {"segment": round((t1 - t0) * 1000, 1), "classify": round((t2 - t1) * 1000, 1)},
        "annotated_image": annotated.name,
    }


def main():
    ap = argparse.ArgumentParser(description="Coffee bean detection (7 classes)")
    ap.add_argument("images", nargs="+", type=Path, help="ภาพหนึ่งภาพหรือหลายภาพของล็อตเดียวกัน")
    ap.add_argument("--lot", default=datetime.now().strftime("LOT-%Y%m%d-%H%M%S"))
    ap.add_argument("--model", default=MODEL)
    args = ap.parse_args()

    from ultralytics import YOLO  # import ตรงนี้เพื่อให้ --help ทำงานเร็ว
    model = YOLO(args.model, task="classify")
    model.predict(np.zeros((IMGSZ, IMGSZ, 3), np.uint8), imgsz=IMGSZ, verbose=False)  # warm-up + โหลดชื่อคลาส
    class_names = list(model.names.values())
    OUT_DIR.mkdir(exist_ok=True)

    t_start = time.perf_counter()
    total = {name: 0 for name in class_names}
    images = []
    for path in args.images:
        info = process_image(model, class_names, path, OUT_DIR)
        for name, n in info["counts"].items():
            total[name] += n
        images.append(info)
        print(f"{path.name}: {info['beans_detected']} เม็ด {info['counts']}  "
              f"(ตัด {info['timing_ms']['segment']} ms · classify {info['timing_ms']['classify']} ms)")

    result = {
        "lot_id": args.lot,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "device_id": DEVICE_ID,
        "model": Path(args.model).name,
        "image_count": len(images),
        "total_beans": sum(total.values()),
        "counts": total,
        "images": images,
        "processing_ms": round((time.perf_counter() - t_start) * 1000, 1),
    }

    out_json = OUT_DIR / f"{args.lot}.json"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nรวม {result['total_beans']} เม็ด · {total}")
    print(f"บันทึก {out_json} และภาพ *_annotated.jpg ใน {OUT_DIR}/")


if __name__ == "__main__":
    main()
