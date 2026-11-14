# ☕ Bean Detector · Edge AI ตรวจจับเมล็ดกาแฟโรบัสต้าดิบ 7 คลาสบน Raspberry Pi 5

ผลงานเตรียมตัวสำหรับ **TESA Top Gun Rally 2026 · Track 2 Edge AI** (KMITL Chumphon)
ระบบรับภาพเมล็ดกาแฟ → แยกเมล็ดทีละเม็ด → จำแนก 7 คลาสด้วย AI บน Raspberry Pi → นับจำนวนต่อคลาส

**ขอบเขตของ Pi:** ตรวจจับ + นับ 7 คลาส แล้วส่งจำนวนต่อคลาสให้ server ผ่าน MQTT · การคิดเกรด / หน้าเว็บ อยู่ที่ฝั่ง server

**โมเดลที่ใช้งานอยู่: v4** · ประวัติและผลของทุกรุ่น: [versions/](versions/README.md)

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
│ 4. ส่งผล      mqtt/send.py → topic coffee/<LOT_ID>/ai_results │
└─────────────────────────────────────────────────────────┘
   │  MQTT
   ▼
Server (คิดเกรด + แสดงผล)
```

## ผลลัพธ์หลัก (v4)

| เรื่อง | ค่า |
|---|---|
| โมเดลหลัก | `cls_v4` · YOLO26n-cls · 60 epochs · imgsz 320 · เทรนด้วย `beans-cls-v4` (ROBUSTA + NIA + CFE) |
| **ความแม่น test ROBUSTA + NIA** | **0.909** (379/417) · ROBUSTA 0.803 · NIA 0.955 |
| test CFE | 0.995 (v3 ได้ 0.410 → v3 พังกับภาพแบบใหม่) |
| คู่ที่ยังสับสน | shell ↔ broken · broken → parchment · good ↔ full_black |
| ความเร็วบน Pi 5 (NCNN) | ~12 ms/เม็ด · ความแม่นบน Pi = บนคอมทุกเม็ด |
| ตัดเมล็ด (OpenCV) | 2 ms/ภาพ · นับตรง label 52/52 เม็ด (พื้นสีอ่อน) |

รายละเอียดและเทียบทุกรุ่น: [versions/README.md](versions/README.md)

## โครงสร้าง repo

```
detector/
  detect.py        ภาพ → ตัดเมล็ด → classify → นับต่อคลาส → JSON + ภาพวาดกรอบ (รันบน Pi)
scripts/
  crop_beans.py    ตัดเมล็ดจาก dataset (YOLO bbox) → dataset classification 7 คลาส (--preset robusta|nia)
  merge_cls.py     รวมหลาย dataset → datasets/beans-cls-v4 (ชุดที่สำเนาภาพรั่วข้าม split ถูกแบ่งใหม่ตามภาพต้นฉบับ)
  eval_cls.py      วัดความแม่นต่อคลาส (ใช้ได้ทั้ง .pt บนคอม และ NCNN บน Pi)
  eval_cls_pi.py   วัดความแม่น + เวลาต่อเม็ดของโมเดล NCNN บน Pi
mqtt/
  send.py          อ่าน JSON จาก detect.py → ส่งจำนวน 7 คลาสไป server
  mqtt.example.yaml  ตัวอย่างตั้งค่า broker (คัดลอกเป็น mqtt.yaml แล้วกรอกค่าจริง · mqtt.yaml ห้าม push)
versions/        โมเดลแต่ละรุ่น + ค่าที่ใช้เทรน + ผลวัด + คำอธิบาย (v1–v3, v4 ✅)
docs/            เอกสาร: คู่มือเริ่มต้น, setup, เส้นทางการทำงาน, dataset
```

## เริ่มใช้งานบน Raspberry Pi

```bash
cd ~/tesa && source .venv/bin/activate
python detector/detect.py full-test/*.jpg --lot TEST-ALL    # ตรวจจับ + นับ
python mqtt/send.py results/TEST-ALL.json                  # ส่งผลไป server
```

- `detect.py` ได้ `results/TEST-ALL.json` (จำนวนต่อคลาสรวมทั้งล็อต + รายเม็ดต่อภาพ) และ `results/*_annotated.jpg`
- `send.py` ต้องมี `mqtt/mqtt.yaml` (คัดลอกจาก `mqtt.example.yaml` แล้วกรอกค่าจริง)

ตัวอย่าง (ตัวเลขสมมติ):

```json
// ส่วนสรุปใน results/TEST-ALL.json
{"lot_id": "TEST-ALL", "total_beans": 52, "counts": {"broken": 6, "full_black": 5, "good": 9, "husk": 15, "immature": 13, "parchment": 2, "shell": 2}}
// payload ที่ส่งไป topic coffee/TEST-ALL/ai_results
{"good": 9, "shell": 2, "full_black": 5, "broken": 6, "parchment": 2, "hull_husk": 15, "immature": 13}
```

ขั้นตอนติดตั้งเต็ม (คอมเทรน + Pi): [docs/setup.md](docs/setup.md)

## เอกสาร

| ไฟล์ | เนื้อหา |
|---|---|
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | **คู่มือเริ่มต้นตั้งแต่ศูนย์** ทีละขั้น + แก้ปัญหา + คำศัพท์ |
| [docs/TRAINING_FLOW.md](docs/TRAINING_FLOW.md) | **ได้ dataset ใหม่ → เทรน → NCNN → Pi** ทีละขั้น พร้อม flowchart |
| [docs/setup.md](docs/setup.md) | ติดตั้งคอม (CUDA) + Raspberry Pi + คำสั่งที่ใช้บ่อย |
| [docs/journey.md](docs/journey.md) | เส้นทางการพัฒนา ปัญหาที่เจอ และวิธีแก้ |
| [docs/datasets.md](docs/datasets.md) | dataset ที่ใช้และข้อจำกัด |
| [versions/README.md](versions/README.md) | โมเดลแต่ละรุ่น ผลเทรน ผลทดสอบบน Pi และเหตุผลที่เปลี่ยนรุ่น |

## ข้อจำกัดที่รู้แล้ว

- ตัดเมล็ดด้วย OpenCV ใช้ได้กับพื้นสีอ่อนเรียบ เมล็ดไม่ติดกัน · กองบนพื้นไม้ต้องใช้โมเดล segmentation (Day 2)
- โมเดลแม่นลดลงกับภาพคนละแบบ (domain shift) → วันจริงต้องเทรนใหม่โดยผสมข้อมูลของผู้จัด

## ที่มาของข้อมูล

- ROBUSTA DATASET (No digkit3) · Renies Workspace · Roboflow Universe · CC BY 4.0
- coffee-bean-defect · niacubilla · Roboflow Universe · CC BY 4.0
- OPTIMIZED GREEN CFE BEANS · green-coffee-beans · Roboflow Universe · CC BY 4.0
- Ultralytics YOLO26 · NCNN (Tencent) · Eclipse Paho MQTT
