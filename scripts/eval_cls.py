"""
eval_cls.py — วัดความแม่นของ classifier กับโฟลเดอร์ภาพเมล็ด (ชื่อโฟลเดอร์ย่อย = คลาสจริง)
ใช้ได้ทั้งบนคอม (.pt) และบน Pi (โฟลเดอร์ _ncnn_model)

ตัวอย่าง (ที่ C:\\tesa-pi ใน venv):
    python scripts\\eval_cls.py --model runs\\classify\\cls_v3\\weights\\best.pt --data datasets\\beans-cls-v3\\test --exclude nia_
    python scripts\\eval_cls.py --model runs\\classify\\cls_v3\\weights\\best.pt --data datasets\\beans-cls-v3\\test --include nia_
"""
import argparse
import time
from collections import Counter
from pathlib import Path

from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--data", required=True, help="โฟลเดอร์ที่มีโฟลเดอร์ย่อยตามคลาส")
    ap.add_argument("--imgsz", type=int, default=320)
    ap.add_argument("--include", default="", help="วัดเฉพาะไฟล์ที่ชื่อขึ้นต้นด้วยคำนี้")
    ap.add_argument("--exclude", default="", help="ข้ามไฟล์ที่ชื่อขึ้นต้นด้วยคำนี้")
    args = ap.parse_args()

    images = sorted(Path(args.data).rglob("*.jpg"))
    if args.include:
        images = [p for p in images if p.name.startswith(args.include)]
    if args.exclude:
        images = [p for p in images if not p.name.startswith(args.exclude)]
    if not images:
        print("ไม่พบภาพตามเงื่อนไข")
        return

    model = YOLO(args.model, task="classify")
    total, correct, wrong_as = Counter(), Counter(), Counter()
    t0 = time.perf_counter()
    for i in range(0, len(images), 64):  # ส่งเป็นชุดละ 64 ภาพ เร็วกว่าทีละภาพ
        batch = images[i:i + 64]
        for img, r in zip(batch, model.predict([str(p) for p in batch], imgsz=args.imgsz, verbose=False)):
            true_cls, pred_cls = img.parent.name, r.names[r.probs.top1]
            total[true_cls] += 1
            if pred_cls == true_cls:
                correct[true_cls] += 1
            else:
                wrong_as[(true_cls, pred_cls)] += 1
    ms = (time.perf_counter() - t0) / len(images) * 1000

    print(f"\nmodel: {args.model}\ndata : {args.data}  include='{args.include}' exclude='{args.exclude}'")
    print(f"\n{'class':<12}{'correct':>9}{'total':>7}{'acc':>8}")
    for c in sorted(total):
        print(f"{c:<12}{correct[c]:>9}{total[c]:>7}{correct[c] / total[c]:>8.2f}")
    n = sum(total.values())
    print(f"\noverall accuracy : {sum(correct.values()) / n:.3f} ({sum(correct.values())}/{n})")
    print(f"time per bean    : {ms:.1f} ms")
    if wrong_as:
        print("\nผิดบ่อยสุด:", ", ".join(f"{t}→{p} {k}" for (t, p), k in wrong_as.most_common(5)))


if __name__ == "__main__":
    main()
