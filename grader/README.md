# ☕ Bean Grader · Edge AI ตรวจคุณภาพเมล็ดกาแฟโรบัสต้าดิบบน Raspberry Pi 5

ผลงานเตรียมตัวสำหรับ **TESA Top Gun Rally 2026 · Track 2 Edge AI** (KMITL Chumphon)
ระบบรับภาพเมล็ดกาแฟ → แยกเมล็ดทีละเม็ด → จำแนก 7 คลาสด้วย AI บน Raspberry Pi → นับ → คำนวณสัดส่วนเมล็ดเสียและเกรด A/B/C → ส่งผลให้ server ผ่าน MQTT

![Bean Grader](examples/ui/bean_grader_nia_full.png)

> 🚀 **เพิ่งเริ่ม? อ่าน [คู่มือเริ่มต้นใช้งานตั้งแต่ศูนย์](docs/GETTING_STARTED.md)** · ติดตั้งคอม + Pi → เทรน → รันเว็บ → ส่ง MQTT ทีละขั้น พร้อมวิธีแก้ปัญหาที่พบบ่อย

## ภาพรวมระบบ

```
ภาพเมล็ดกาแฟ
   │
   ▼  Raspberry Pi 5 (CPU ล้วน ไม่ใช้บอร์ดเร่ง AI)
┌─────────────────────────────────────────────────────────┐
│ 1. ตัดเมล็ด   OpenCV: Otsu threshold → contour → crop   │
│ 2. จำแนก      YOLO26n-cls (NCNN) · 7 คลาส · ~12 ms/เม็ด  │
│ 3. นับ + เกรด  grade.py: full defects (SCA/CQI) → A/B/C │
│ 4. แสดงผล     หน้าเว็บ Gradio (Bean Grader)             │
└─────────────────────────────────────────────────────────┘
   │  MQTT  topic coffee/<LOT_ID>/ai_results
   ▼
Server / Next-Gen Market (Track 3)
```

## ผลลัพธ์หลัก

| เรื่อง | ค่า |
|---|---|
| โมเดล | YOLO26n-cls · 1.53M params · 3.2 GFLOPs · imgsz 320 |
| ความแม่น (val / test) | 86.5% / 79.5% |
| NCNN บน Pi เทียบ PyTorch บนคอม | ความแม่นเท่ากัน (0.795 = 0.795) |
| ความเร็วบน Pi 5 | 11.7 ms/เม็ด · กอง 50 เม็ด ≈ 0.6 s |
| ตัดเมล็ด (OpenCV) | 2 ms/ภาพ · นับตรง label 52/52 เม็ด (พื้นสีอ่อน) |
| ทดสอบ pipeline โมเดล coco8-seg บน Pi | 122 ms/ภาพ · RAM 0.87 GB |

รายละเอียด: [docs/results.md](docs/results.md)

## โครงสร้าง repo

```
grader/          โปรแกรมหลัก (รันบน Pi)
  app.py           หน้าเว็บ Bean Grader (Gradio)
  pipeline.py      ภาพ → ตัดเมล็ด → classify → นับ → เกรด → JSON + ภาพวาดกรอบ
  grade.py         สูตรเกรด A/B/C (มี self-test)
  grading.yaml     เกณฑ์เกรด (แก้ที่นี่ที่เดียว)
  send.py          ส่งผลผ่าน MQTT ตามสเปก server
  mqtt.yaml        ตั้งค่า broker / topic / ชื่อฟิลด์
scripts/
  crop_beans.py    ตัดเมล็ดจาก dataset (YOLO bbox) → dataset classification 7 คลาส
  eval_cls_pi.py   วัดความแม่น + เวลาต่อเม็ดของโมเดล NCNN บน Pi
models/          ใส่ cls_v2.pt (โมเดลที่เทรนแล้ว)
docs/            เอกสาร: setup, เส้นทางการทำงาน, เกณฑ์เกรด, dataset, ผลทดสอบ
examples/        ภาพผลจริง, JSON ตัวอย่าง, confusion matrix, หน้าจอโปรแกรม
```

## เริ่มใช้งานบน Raspberry Pi

```bash
cd ~/tesa && source .venv/bin/activate
python grader/grade.py          # ทดสอบสูตรเกรด (ต้องขึ้น PASS 5/5)
python grader/app.py            # เปิดเว็บ → http://<IP ของ Pi>:7860
python grader/pipeline.py full-test/*.jpg --lot TEST-ALL   # รันแบบ command line
```

ขั้นตอนติดตั้งเต็ม (คอมเทรน + Pi): [docs/setup.md](docs/setup.md)

## ข้อมูลที่ส่งให้ server (MQTT)

- Topic: `coffee/<LOT_ID>/ai_results` · JSON · QoS 1
- `defect_ratio` เป็นเปอร์เซ็นต์ ทศนิยม 2 ตำแหน่ง (DECIMAL(5,2) ใน MySQL)

```json
{"good": 9, "shell": 0, "full_black": 5, "broken": 0, "parchment": 2, "hull_husk": 15, "immature": 21, "defect_ratio": 82.69}
```

## เอกสาร

| ไฟล์ | เนื้อหา |
|---|---|
| [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) | **คู่มือเริ่มต้นตั้งแต่ศูนย์** ทีละขั้น + แก้ปัญหา + คำศัพท์ |
| [docs/setup.md](docs/setup.md) | ติดตั้งคอม (CUDA) + Raspberry Pi + คำสั่งที่ใช้บ่อย |
| [docs/journey.md](docs/journey.md) | เส้นทางการพัฒนา ปัญหาที่เจอ และวิธีแก้ |
| [docs/grading.md](docs/grading.md) | เกณฑ์เกรด A/B/C และที่มา |
| [docs/datasets.md](docs/datasets.md) | dataset ที่ใช้และข้อจำกัด |
| [docs/results.md](docs/results.md) | ผลเทรน ผลทดสอบบน Pi และข้อสังเกต |

## ข้อจำกัดที่รู้แล้ว

- ตัดเมล็ดด้วย OpenCV ใช้ได้กับพื้นสีอ่อนเรียบ เมล็ดไม่ติดกัน · กองบนพื้นไม้ต้องใช้โมเดล segmentation
- classifier เรียนจาก dataset เดียว (DSLR พื้นขาว) ภาพคนละแบบความแม่นลดชัดเจน → วันจริงต้องเทรนใหม่ด้วยข้อมูลของผู้จัด
- เกรดเป็นเกรดทางกายภาพเท่านั้น (ไม่รวมความชื้นและการชิม)

## ที่มาของข้อมูล

- ROBUSTA DATASET (No digkit3) · Renies Workspace · Roboflow Universe · CC BY 4.0
- coffee-bean-defect · niacubilla · Roboflow Universe · CC BY 4.0 (ใช้ทดสอบ)
- เกณฑ์ full defect: SCA / CQI (Fine Robusta) · มาตรฐานไทย มกษ. 5700-2561
- Ultralytics YOLO26 · NCNN (Tencent) · Gradio · Eclipse Paho MQTT
