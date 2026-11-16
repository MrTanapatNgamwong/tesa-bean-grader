# 📦 เวอร์ชันของโมเดล

แต่ละโฟลเดอร์ = โมเดลหนึ่งรุ่น พร้อมไฟล์โมเดล ค่าที่ใช้เทรน และผลวัด · **ตัวที่ใช้งานอยู่ตอนนี้คือ v6**

| รุ่น | วันที่ | ข้อมูลเทรน | ตั้งค่า | ผลหลัก | สถานะ |
|---|---|---|---|---|---|
| [v1](v1/) | 10 พ.ย. 2569 | ROBUSTA (`beans-cls`) | 30 epochs · imgsz 224 | val 0.865 | เลิกใช้ · ไม่มีไฟล์โมเดลเหลือ |
| [v2](v2/) | 10–11 พ.ย. 2569 | ROBUSTA (`beans-cls`) | 60 epochs · imgsz 320 | val 0.865 · test 0.795 · NIA 0.693 | เลิกใช้ · เก็บไว้เทียบ |
| [v3](v3/) | 12 พ.ย. 2569 | ROBUSTA + NIA (`beans-cls-v3`) | 60 epochs · imgsz 320 | test ROBUSTA 0.787 · NIA 0.959 | เลิกใช้ · เก็บไว้เทียบ |
| [v4](v4/) | 14 พ.ย. 2569 | ROBUSTA + NIA + CFE (`beans-cls-v4`) | 60 epochs · imgsz 320 | test ROBUSTA 0.803 · NIA 0.955 · รวม 0.909 · CFE 0.995 · PHONE 0.581 | เลิกใช้ · เก็บไว้เทียบ |
| [v5](v5/) | 15 พ.ย. 2569 | ROBUSTA + NIA + CFE + PHONE (`beans-cls-v5`) | 60 epochs · imgsz 320 | test ROBUSTA 0.819 · NIA 0.955 · รวม 0.914 · CFE 0.995 · **PHONE 0.925** | เลิกใช้ · เก็บไว้เทียบ |

| [v6](v6/) ✅ | 16 พ.ย. 2569 | ROBUSTA + NIA + CFE + PHONE + testsssss (`beans-cls-v6`) | 60 epochs · imgsz 320 | test ROBUSTA 0.795 · NIA 0.959 · รวม 0.909 · CFE 0.994 · PHONE 0.943 · **testsssss 0.890** (v5 ได้ 0.251) | **ใช้งานอยู่** |

ทุกรุ่นคือ YOLO26n-cls (จำแนกเมล็ดทีละเม็ด 7 คลาส) เริ่มจาก `yolo26n-cls.pt`

## ระบบ (โค้ด) แต่ละช่วง

| ช่วง | โค้ดบน Pi | ดูโค้ดย้อนหลัง |
|---|---|---|
| v2 · ระบบเกรด | `grader/`: ตัดเมล็ด → classify → นับ → เกรด A/B/C → หน้าเว็บ Gradio → MQTT | `git checkout v2-grader` |
| v3–v6 · ตรวจจับอย่างเดียว | `detector/detect.py`: ตัดเมล็ด → classify → นับต่อคลาส · `mqtt/send.py` ส่งจำนวนต่อคลาส · เกรดคิดที่ server | `main` ปัจจุบัน |

## ทำรุ่นใหม่ (เช่น v7)

ทำตาม [docs/TRAINING_FLOW.md](../docs/TRAINING_FLOW.md) · สรุป:

1. เตรียมข้อมูลใหม่ → ตั้งชื่อ dataset ใหม่ เช่น `datasets/beans-cls-v7` (อย่าเขียนทับ `beans-cls-v6`)
2. เทรนด้วย `name=cls_v7` → ได้ `runs\classify\cls_v7\`
3. สร้างโฟลเดอร์ `versions/v7/` คัดลอก `best.pt` → `strip_optimizer` แล้วตั้งชื่อ `cls_v7.pt`, `args.yaml`, `results.csv`, `results.png`, `confusion_matrix*.png`
4. เขียน `versions/v7/README.md` ตามแบบ v6 แล้วเพิ่มแถวในตารางด้านบน
5. ถ้าดีกว่า v6 → เปลี่ยน `MODEL` ใน `detector/detect.py` และย้ายเครื่องหมาย ✅
