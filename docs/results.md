# ผลลัพธ์

## Classifier (YOLO26n-cls)

| รุ่น | ตั้งค่า | top1 val | top1 test |
|---|---|---|---|
| cls_v1 | 30 epochs · imgsz 224 | 0.865 | — |
| cls_v2 | 60 epochs · imgsz 320 · ROBUSTA | 0.865 | 0.795 |
| cls_v3 ✅ | 60 epochs · imgsz 320 · ROBUSTA + NIA (`beans-cls-v3`) | — | ROBUSTA 0.787 · NIA 0.959 |

cls_v3 เทียบ cls_v2: ROBUSTA ลดเล็กน้อย (0.795 → 0.787) แต่ NIA ดีขึ้นมาก (0.693 → 0.959) → ทนต่อภาพคนละแบบมากขึ้น · ยังสับสน good ↔ full_black และ shell ↔ broken

ตารางต่อคลาส (cls_v1 / cls_v2 · val):

| คลาส | v1 | v2 |
|---|---|---|
| husk | 1.00 | 1.00 |
| full_black | 0.93 | 0.96 |
| broken | 0.84 | 0.89 |
| good | 0.88 | 0.85 |
| immature | 0.78 | 0.78 |
| parchment | 0.57 | 0.71 |
| shell | 0.57 | 0.39 |

Confusion matrix: [v1](../examples/evaluation/cls_v1_confusion_matrix.png) · [v2](../examples/evaluation/cls_v2_confusion_matrix.png)

ข้อสังเกต: คู่ที่สับสนบ่อยคือ shell ↔ broken และ good ↔ full_black · ต้องแก้ด้วยข้อมูลเพิ่มของคลาสเหล่านี้

## บน Raspberry Pi 5

| การทดสอบ | ผล |
|---|---|
| cls_v2 NCNN · test 127 เม็ด | 0.795 (เท่ากับ PyTorch บนคอม) · 11.7 ms/เม็ด |
| cls_v3 NCNN | ~5–12 ms/เม็ด |
| ตัด + classify ทั้งสาย · 44 ภาพ ROBUSTA test (cls_v2) | 265 เม็ด · ตัด 2 ms/ภาพ · classify ~101 ms/ภาพ · รวม 4.7 s |
| coco8-seg NCNN (Milestone) | 122 ms/ภาพ · RAM 0.87 GB |

## ทดสอบกับ dataset อื่น (coffee-bean-defect) · ก่อนเทรน cls_v3

| | label จริง | ระบบ |
|---|---|---|
| ภาพเมล็ดดีล้วน 34 ภาพ: จำนวนเมล็ด | 52 | 52 ✅ |
| เมล็ดดี | 52 | 9 ❌ |

สรุป: ส่วนตัดเมล็ดและนับถูกต้อง · classifier (cls_v2) ต้องเทรนเพิ่มด้วยข้อมูลหลายแบบ → จึงทำ cls_v3 ที่ผสม NIA เข้าไป
