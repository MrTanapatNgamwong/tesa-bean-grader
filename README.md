# ☕ Bean Detector · Edge AI ตรวจจับเมล็ดกาแฟโรบัสต้าดิบ 7 คลาสบน Raspberry Pi 5

ผลงานเตรียมตัวสำหรับ **TESA Top Gun Rally 2026 · Track 2 Edge AI** (KMITL Chumphon)
ระบบรับภาพเมล็ดกาแฟ → แยกเมล็ดทีละเม็ด → จำแนก 7 คลาสด้วย AI บน Raspberry Pi → นับจำนวนต่อคลาส

**ขอบเขตของ Pi:** ตรวจจับและนับเท่านั้น · การคิดเกรด / หน้าเว็บ อยู่ที่ฝั่ง server · การส่งผลไป server ผ่าน MQTT จะออกแบบในขั้นถัดไป

> 🚀 **เพิ่งเริ่ม? อ่าน [คู่มือเริ่มต้นใช้งานตั้งแต่ศูนย์](docs/GETTING_STARTED.md)** · ติดตั้งคอม + Pi → เทรน → export → รันบน Pi ทีละขั้น

**7 คลาส:** good · shell · full_black · husk (hull/husk) · broken · parchment · immature

## ภาพรวมระบบ

```
ภาพเมล็ดกาแฟ
   │
   ▼  Raspberry Pi 5 (CPU ล้วน ไม่ใช้บอร์ดเร่ง AI)
┌─────────────────────────────────────────────────────────┐
│ 1. ตัดเมล็ด   OpenCV: Otsu threshold → contour → crop   │
│ 2. จำแนก      YOLO26n-cls (NCNN) · 7 คลาส · ~5–12 ms/เม็ด │
│ 3. นับ        จำนวนเมล็ดต่อคลาส → JSON + ภาพวาดกรอบ      │
└─────────────────────────────────────────────────────────┘
   │  (ขั้นถัดไป) MQTT
   ▼
Server (คิดเกรด + แสดงผล)
```

## ผลลัพธ์หลัก

| เรื่อง | ค่า |
|---|---|
| โมเดลหลัก | `cls_v3` · YOLO26n-cls · 60 epochs · imgsz 320 · เทรนด้วย `beans-cls-v3` (ROBUSTA + NIA) |
| ความแม่น test ROBUSTA / NIA | 0.787 / 0.959 (cls_v2: 0.795 / 0.693) |
| คู่ที่ยังสับสน | good ↔ full_black · shell ↔ broken |
| ความเร็วบน Pi 5 (NCNN) | ~5–12 ms/เม็ด |
| NCNN บน Pi เทียบ PyTorch บนคอม | ความแม่นเท่ากัน (ทดสอบกับ cls_v2: 0.795 = 0.795) |
| ตัดเมล็ด (OpenCV) | 2 ms/ภาพ · นับตรง label 52/52 เม็ด (พื้นสีอ่อน) |

รายละเอียด: [docs/results.md](docs/results.md)

## โครงสร้าง repo

```
detector/
  detect.py        ภาพ → ตัดเมล็ด → classify → นับต่อคลาส → JSON + ภาพวาดกรอบ (รันบน Pi)
scripts/
  crop_beans.py    ตัดเมล็ดจาก dataset (YOLO bbox) → dataset classification 7 คลาส (--preset robusta|nia)
  merge_cls.py     รวม ROBUSTA + NIA → datasets/beans-cls-v3 (NIA แบ่งใหม่ตามภาพต้นฉบับ)
  eval_cls.py      วัดความแม่นต่อคลาส (ใช้ได้ทั้ง .pt บนคอม และ NCNN บน Pi)
  eval_cls_pi.py   วัดความแม่น + เวลาต่อเม็ดของโมเดล NCNN บน Pi
models/          cls_v3.pt (ตัวหลัก) · cls_v2.pt (รุ่นก่อน)
docs/            เอกสาร: คู่มือเริ่มต้น, setup, เส้นทางการทำงาน, dataset, ผลทดสอบ
examples/        ภาพผลจริง (annotated), confusion matrix
```

## เริ่มใช้งานบน Raspberry Pi

```bash
cd ~/tesa && source .venv/bin/activate
python detector/detect.py full-test/*.jpg --lot TEST-ALL
```

ได้ `results/TEST-ALL.json` (จำนวนต่อคลาสรวมทั้งล็อต + รายเม็ดต่อภาพ) และ `results/*_annotated.jpg`

ตัวอย่างส่วนสรุปใน JSON (ตัวเลขสมมติ):

```json
{"lot_id": "TEST-ALL", "total_beans": 52, "counts": {"broken": 6, "full_black": 5, "good": 9, "husk": 15, "immature": 13, "parchment": 2, "shell": 2}}
```

ขั้นตอนติดตั้งเต็ม (คอมเทรน + Pi): [docs/setup.md](docs/setup.md)

## เอกสาร

| ไฟล์ | เนื้อหา |
|---|---|
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | **คู่มือเริ่มต้นตั้งแต่ศูนย์** ทีละขั้น + แก้ปัญหา + คำศัพท์ |
| [docs/setup.md](docs/setup.md) | ติดตั้งคอม (CUDA) + Raspberry Pi + คำสั่งที่ใช้บ่อย |
| [docs/journey.md](docs/journey.md) | เส้นทางการพัฒนา ปัญหาที่เจอ และวิธีแก้ |
| [docs/datasets.md](docs/datasets.md) | dataset ที่ใช้และข้อจำกัด |
| [docs/results.md](docs/results.md) | ผลเทรน ผลทดสอบบน Pi และข้อสังเกต |

## ข้อจำกัดที่รู้แล้ว

- ตัดเมล็ดด้วย OpenCV ใช้ได้กับพื้นสีอ่อนเรียบ เมล็ดไม่ติดกัน · กองบนพื้นไม้ต้องใช้โมเดล segmentation (Day 2)
- โมเดลแม่นลดลงกับภาพคนละแบบ (domain shift) → วันจริงต้องเทรนใหม่โดยผสมข้อมูลของผู้จัด

## ที่มาของข้อมูล

- ROBUSTA DATASET (No digkit3) · Renies Workspace · Roboflow Universe · CC BY 4.0
- coffee-bean-defect · niacubilla · Roboflow Universe · CC BY 4.0
- Ultralytics YOLO26 · NCNN (Tencent)
