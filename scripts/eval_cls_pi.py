"""
eval_cls_pi.py — ทดสอบ classifier (NCNN) บน Raspberry Pi
วัด 2 อย่าง: ความแม่นต่อคลาส และเวลาที่ใช้ต่อเมล็ด

โครงสร้างข้อมูลที่ต้องมี (ชื่อโฟลเดอร์ย่อย = คลาสจริง):
    beans-test/good/*.jpg, beans-test/shell/*.jpg, ...

วิธีรัน (บน Pi ใน venv):
    cd ~/tesa
    python eval_cls_pi.py
"""
import time
from collections import Counter
from pathlib import Path

from ultralytics import YOLO

# ===== ตั้งค่า =====
MODEL = "cls_v4_ncnn_model"  # โฟลเดอร์โมเดล NCNN (ชื่อต้องลงท้าย _ncnn_model)
DATA = Path("beans-test")  # โฟลเดอร์ภาพทดสอบ
IMGSZ = 320                # ต้องตรงกับตอนเทรน/export


def main():
    model = YOLO(MODEL, task="classify")
    images = sorted(DATA.rglob("*.jpg"))
    if not images:
        print("ไม่พบภาพใน", DATA.resolve())
        return

    # รอบแรกช้ากว่าปกติ (โหลดโมเดลเข้าหน่วยความจำ) จึงรันทิ้งหนึ่งครั้งก่อนจับเวลา
    model.predict(str(images[0]), imgsz=IMGSZ, verbose=False)

    total, correct, times = Counter(), Counter(), []
    for img in images:
        true_cls = img.parent.name
        t0 = time.perf_counter()
        r = model.predict(str(img), imgsz=IMGSZ, verbose=False)[0]
        times.append(time.perf_counter() - t0)
        pred_cls = r.names[r.probs.top1]
        total[true_cls] += 1
        correct[true_cls] += pred_cls == true_cls

    # ===== สรุปผล =====
    print(f"\n{'class':<12}{'correct':>9}{'total':>7}{'acc':>8}")
    for cls in sorted(total):
        print(f"{cls:<12}{correct[cls]:>9}{total[cls]:>7}{correct[cls] / total[cls]:>8.2f}")
    n = sum(total.values())
    avg_ms = sum(times) / len(times) * 1000
    print(f"\noverall accuracy : {sum(correct.values()) / n:.3f} ({sum(correct.values())}/{n})")
    print(f"time per bean    : {avg_ms:.1f} ms (เฉลี่ยจาก {len(times)} เม็ด)")
    print(f"pile of 50 beans : ~{avg_ms * 50 / 1000:.1f} s (เฉพาะส่วน classify)")


if __name__ == "__main__":
    main()
