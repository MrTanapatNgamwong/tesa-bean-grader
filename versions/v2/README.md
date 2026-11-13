# v2 · เพิ่ม epochs + ขนาดภาพ (เลิกใช้ · เก็บไว้เทียบ)

- **วันที่:** 10–11 พ.ย. 2569
- **ข้อมูล:** `datasets/beans-cls` (ROBUSTA อย่างเดียว · ชุดเดียวกับ v1)
- **ตั้งค่า:** YOLO26n-cls · 60 epochs · imgsz 320
- **ไฟล์ในโฟลเดอร์:**
  - `cls_v2.pt` · โมเดล
  - `confusion_matrix_normalized.png`
  - `annotated/` · ตัวอย่างภาพที่ pipeline วาดกรอบ + คลาส (ภาพ ROBUSTA test)

```bat
yolo classify train model=yolo26n-cls.pt data=datasets/beans-cls epochs=60 imgsz=320 device=0 name=cls_v2
```

## ผล

| การทดสอบ | ผล |
|---|---|
| top1 val | 0.865 (เท่า v1) |
| top1 test ROBUSTA (127 เม็ด) | 0.795 |
| NCNN บน Pi เทียบ PyTorch บนคอม | 0.795 = 0.795 → แปลงเป็น NCNN ไม่ทำให้แม่นลด |
| ความเร็วบน Pi 5 (NCNN) | 11.7 ms/เม็ด · กอง 50 เม็ด ≈ 0.6 s |
| ทั้งสายบน Pi · 44 ภาพ ROBUSTA test | 265 เม็ด · ตัด 2 ms/ภาพ · classify ~101 ms/ภาพ · รวม 4.7 s |
| ภาพจาก dataset อื่น (NIA) | test NIA 0.693 · ภาพเมล็ดดีล้วน 34 ภาพ: ตัดเมล็ดตรง 52/52 แต่ทายเมล็ดดีถูกแค่ 9/52 |

## ความแม่นต่อคลาส (val)

| คลาส | v1 | v2 |
|---|---|---|
| husk | 1.00 | 1.00 |
| full_black | 0.93 | 0.96 |
| broken | 0.84 | 0.89 |
| good | 0.88 | 0.85 |
| immature | 0.78 | 0.78 |
| parchment | 0.57 | 0.71 |
| shell | 0.57 | 0.39 |

**ข้อสังเกต:** ภาพรวมไม่ดีขึ้น · full_black ดีขึ้น · shell แย่ลง (สับสนกับ broken)

**ทำไมไปต่อ v3:** โมเดลเก่งเฉพาะภาพแบบ ROBUSTA (DSLR พื้นขาว) เจอภาพคนละแบบแม่นลดมาก (domain shift) → ต้องผสมข้อมูลหลายแบบ

## ระบบในช่วงนี้

ช่วง v2 ระบบบน Pi เป็น **Bean Grader**: คิดเกรด A/B/C (`grade.py`, `grading.yaml`) + หน้าเว็บ Gradio (`app.py`) + ส่ง MQTT พร้อม `defect_ratio` · ภายหลังย้ายเรื่องเกรด/หน้าเว็บไปฝั่ง server · ดูโค้ดชุดนั้นด้วย `git checkout v2-grader`
