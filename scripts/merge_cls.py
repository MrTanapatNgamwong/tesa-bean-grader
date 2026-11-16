"""
merge_cls.py — รวม dataset classification หลายชุดเป็นชุดเดียวสำหรับเทรน cls_v3

- ROBUSTA (beans-cls): ใช้การแบ่ง train/val/test เดิม
- NIA (beans-cls-nia): ชุดเดิมแบ่งไม่สมดุล (val ไม่มีเมล็ดดี) และภาพต้นฉบับทุกภาพมี 2 สำเนาอยู่คนละ split
  (ข้อมูลรั่วระหว่าง train/test) → เทใหม่หมดแล้วแบ่ง 80/10/10
  แบ่งตาม "ภาพต้นฉบับ" ไม่ใช่ทีละเม็ด กันเมล็ดจากภาพเดียวกันไปอยู่ทั้ง train และ test

วิธีรัน (ที่ C:\\tesa-pi ใน venv):
    python scripts\\merge_cls.py
"""
import random
import shutil
from collections import defaultdict
from pathlib import Path

KEEP_SPLIT = [Path("datasets/beans-cls"), Path("datasets/beans-cls-tss")]
RESPLIT = [Path("datasets/beans-cls-nia"), Path("datasets/beans-cls-cfe"), Path("datasets/beans-cls-phone")]
DST = Path("datasets/beans-cls-v6")
RATIO = (0.8, 0.1, 0.1)                           # train / val / test
SEED = 42                                         # ค่าสุ่มคงที่ = รันซ้ำได้ผลเหมือนเดิม
SPLITS = ["train", "val", "test"]


def source_of(path):
    """ชื่อไฟล์ <ภาพ>.rf.<รหัส>_<ลำดับเม็ด>.jpg → <ภาพต้นฉบับ>
    Roboflow ใส่ .rf.<รหัส> ให้ทุกสำเนา ภาพต้นฉบับเดียวกันจึงต้องตัดส่วนนี้ทิ้งก่อนจัดกลุ่ม"""
    return path.stem.rsplit("_", 1)[0].split(".rf.")[0]


def main():
    if DST.exists():
        shutil.rmtree(DST)  # สร้างใหม่ทุกครั้ง กันไฟล์เก่าค้าง
    counts = defaultdict(int)

    # 1) ชุดที่ใช้การแบ่งเดิม: คัดลอกตรง ๆ
    for root in KEEP_SPLIT:
        for split in SPLITS:
            for f in (root / split).glob("*/*.jpg"):
                out = DST / split / f.parent.name
                out.mkdir(parents=True, exist_ok=True)
                shutil.copy(f, out / f.name)
                counts[(root.name, split, f.parent.name)] += 1

    # 2) ชุดที่แบ่งใหม่: รวมทุก split → จัดกลุ่มตามภาพต้นฉบับ → สุ่มแบ่ง
    rng = random.Random(SEED)
    for root in RESPLIT:
        groups = defaultdict(list)
        for f in root.glob("*/*/*.jpg"):
            groups[source_of(f)].append(f)
        sources = sorted(groups)
        rng.shuffle(sources)
        n = len(sources)
        cut1, cut2 = int(n * RATIO[0]), int(n * (RATIO[0] + RATIO[1]))
        assign = {s: ("train" if i < cut1 else "val" if i < cut2 else "test") for i, s in enumerate(sources)}
        for src, files in groups.items():
            split = assign[src]
            for f in files:
                out = DST / split / f.parent.name
                out.mkdir(parents=True, exist_ok=True)
                shutil.copy(f, out / f.name)
                counts[(root.name, split, f.parent.name)] += 1

    # 3) สรุป
    classes = sorted({c for _, _, c in counts})
    for root in KEEP_SPLIT + RESPLIT:
        print(f"\n[{root.name}]")
        print(f"{'class':<12}" + "".join(f"{s:>8}" for s in SPLITS))
        for c in classes:
            print(f"{c:<12}" + "".join(f"{counts[(root.name, s, c)]:>8}" for s in SPLITS))
    print(f"\n[รวม → {DST}]")
    print(f"{'class':<12}" + "".join(f"{s:>8}" for s in SPLITS))
    for c in classes:
        print(f"{c:<12}" + "".join(f"{sum(counts[(r.name, s, c)] for r in KEEP_SPLIT + RESPLIT):>8}" for s in SPLITS))


if __name__ == "__main__":
    main()
