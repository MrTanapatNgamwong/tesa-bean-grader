# v6 · เพิ่ม dataset testsssss (shell / parchment / immature) (✅ ใช้งานอยู่)

- **วันที่:** 16 พ.ย. 2569
- **ข้อมูล:** `datasets/beans-cls-v6` = ROBUSTA + NIA + CFE + PHONE (ชุดเดียวกับ v5) + **testsssss** (ใหม่)
- **ตั้งค่า:** YOLO26n-cls · 60 epochs · imgsz 320 · batch 16 · seed 0 (เหมือน v5 ทุกค่า ต่างกันแค่ข้อมูล · ค่าเต็มดู `args.yaml`) · เทรน ~103 นาที บน RTX 4060
- **เริ่มจาก:** `yolo26n-cls.pt`
- **บน Pi:** `cls_v6_ncnn_model` · PHONE test 250/265 = **0.943** ตรงกับบนคอมทุกเม็ด (v5 เคยต่าง 1 เม็ด) · ~17.7 ms/เม็ด
- **หมายเหตุการเทรน:** รอบแรกถูกหยุดจากภายนอกที่ epoch 35 แล้ว `resume` ต่อจาก `last.pt` ถึง epoch 60 → `args.yaml` จึงมี `resume:` ติดมา (พารามิเตอร์อื่นเหมือน v5 ทุกค่า)

## dataset ใหม่: testsssss (rt-pee)

- ได้มาจาก `Theeramet01/tesa-bean-grader` (`HANDOFF.md`) · Roboflow `rt-pee/testsssss-jhgg2` v1 · **CC BY 4.0**
- 263 ภาพ (train 184 / valid 53 / test 26) · 512×512 ยืดจากภาพแนวตั้ง · พื้นขาวเทา · 15–107 เมล็ด/ภาพ
- 6 คลาส: black, broken, immature, normal, parchment, shell · **ไม่มี husk** (preset `tss` ใน `crop_beans.py`)
- **เหตุผลที่เอาเข้า:** อุดช่องว่างที่ v5 ระบุไว้เอง — shell / parchment / immature ยังมาจาก ROBUSTA แหล่งเดียว
- **ตรวจข้อมูลรั่วก่อนใช้:** 263 ภาพ = 263 ต้นฉบับไม่ซ้ำ · md5 ซ้ำข้าม split = 0 · ชื่อต้นฉบับซ้ำข้าม split = 0 → ใส่ `KEEP_SPLIT` (ต่างจาก NIA / CFE ที่ต้องแบ่งใหม่)

| คลาสรวม | v5 train | v6 train | เปลี่ยน |
|---|---|---|---|
| shell | 667 | 2,687 | ×4.0 |
| immature | 918 | 2,661 | ×2.9 |
| parchment | 403 | 1,122 | ×2.8 |
| broken | 5,517 | 7,720 | +40% |
| full_black | 10,800 | 11,634 | +8% |
| good | 8,952 | 9,210 | +3% |
| husk | 6,750 | 6,750 | เท่าเดิม |

## สร้าง dataset + เทรน

```bat
python scripts\crop_beans.py --preset tss --src datasets/testsssss --dst datasets/beans-cls-tss --prefix tss
python scripts\merge_cls.py
yolo classify train model=yolo26n-cls.pt data=datasets/beans-cls-v6 epochs=60 imgsz=320 batch=16 seed=0 device=0 name=cls_v6
yolo export model=runs\classify\cls_v6\weights\cls_v6.pt format=ncnn imgsz=320
```

`merge_cls.py`: `KEEP_SPLIT = [beans-cls, beans-cls-tss]` · `RESPLIT = [beans-cls-nia, beans-cls-cfe, beans-cls-phone]` · `DST = beans-cls-v6`
· testsssss ใช้การแบ่งเดิมของ Roboflow · NIA / CFE / PHONE แบ่งเหมือน v5 ทุกภาพ (SEED เดิม) → **test ของ v6 = test ของ v5 ทุกไฟล์ + tss 1,046 เม็ด** จึงเทียบกับ v5 ได้ตรง

## ผล (test · วัดทั้งสองรุ่นด้วยภาพชุดเดียวกัน)

| test | v5 | v6 |
|---|---|---|
| **testsssss (1,046)** | 0.251 | **0.890** |
| **PHONE (พื้นไม้, 265)** | 0.925 | **0.943** |
| NIA (290) | 0.955 | **0.959** |
| CFE (2,766) | 0.995 | 0.994 |
| ROBUSTA (127) | **0.819** | 0.795 |
| **ROBUSTA + NIA (417)** | **0.914** | 0.909 |
| top1 val (ชุด v6) | — | 0.953 (epoch 60) |

**บน Pi (NCNN):** PHONE 250/265 = **0.943** · ต่างจากบนคอม **0 เม็ด** · ~17.7 ms/เม็ด · ต่อคลาสและรูปแบบที่ทายผิดตรงกับบนคอมทั้งหมด

```bat
python scripts\eval_cls.py --model runs\classify\cls_v6\weights\cls_v6.pt --data datasets\beans-cls\test
python scripts\eval_cls.py --model runs\classify\cls_v6\weights\cls_v6.pt --data datasets\beans-cls-v6\test --include nia_
python scripts\eval_cls.py --model runs\classify\cls_v6\weights\cls_v6.pt --data datasets\beans-cls-v6\test --include cfe_
python scripts\eval_cls.py --model runs\classify\cls_v6\weights\cls_v6.pt --data datasets\beans-cls-v6\test --include phone_
python scripts\eval_cls.py --model runs\classify\cls_v6\weights\cls_v6.pt --data datasets\beans-cls-v6\test --include tss_
```

### ความแม่นต่อคลาส · testsssss test

| คลาส | จำนวน | v5 | v6 |
|---|---|---|---|
| shell | 280 | 0.01 | **0.84** |
| immature | 236 | 0.00 | **0.92** |
| parchment | 103 | 0.01 | **0.88** |
| broken | 277 | 0.74 | **0.89** |
| full_black | 120 | 0.35 | **0.94** |
| good | 30 | 0.40 | **1.00** |

### ความแม่นต่อคลาส · ROBUSTA test

| คลาส | จำนวน | v5 | v6 |
|---|---|---|---|
| full_black | 35 | 1.00 | 1.00 |
| husk | 27 | 1.00 | 1.00 |
| parchment | 7 | 0.71 | 0.71 |
| immature | 11 | 0.73 | 0.64 |
| good | 13 | 0.69 | 0.69 |
| broken | 24 | 0.67 | 0.58 |
| shell | 10 | 0.40 | 0.40 |

### ความแม่นต่อคลาส · PHONE test

| คลาส | จำนวน | v5 | v6 |
|---|---|---|---|
| good | 104 | 0.98 | **0.99** |
| husk | 149 | 0.95 | **0.97** |
| full_black | 8 | 0.25 | 0.25 |
| shell | 3 | 0.00 | 0.00 |
| broken | 1 | 0.00 | 0.00 |

## ข้อสังเกต

- **ได้ผลเฉพาะในโดเมนของข้อมูลใหม่ ไม่ถ่ายทอดข้ามโดเมน:** บน testsssss คลาส shell / immature / parchment พุ่งจาก ~0 เป็น 0.84–0.92 แต่บน ROBUSTA ทั้งสามคลาส **เท่าเดิมหรือลง 1 เม็ด** (shell 4/10 · parchment 5/7 · immature 8→7) → สมมติฐาน "เพิ่มข้อมูลคลาสนั้น แล้วคลาสนั้นดีขึ้นทุกฉาก" ไม่เป็นจริง
- เหตุน่าจะเป็นข้อจำกัดของ testsssss: **ทุกภาพมีคลาสเดียว** (ถ่ายเป็นกองแยกชนิด) โมเดลเรียนฉาก/แสงของกองนั้นได้ แต่ไม่ได้เรียนรูปเมล็ดที่ใช้ข้ามฉาก
- **ROBUSTA เสีย 3 เม็ดจาก 127** (broken −2 · immature −1) อยู่ในระดับที่ขยับเองได้ตามที่บันทึกไว้ใน v5 · ROBUSTA test มี shell 10 · parchment 7 · immature 11 เม็ด **น้อยเกินกว่าจะวัดการดีขึ้นได้จริง**
- **PHONE ขึ้น 0.925 → 0.943** คือชุดที่ใกล้สภาพวันจริงที่สุด · full_black / shell / broken บนพื้นไม้ยังทายไม่ได้ (test มี 1–8 เม็ด) ยังเป็นปัญหาเดิมจาก v5
- เลือกใช้ v6 เพราะครอบคลุมโดเมนกว้างกว่า (v5 ตาบอดสนิทบน testsssss ที่ 0.251) โดยไม่มีสัญญาณว่าแย่ลงจริงในทางปฏิบัติ

## ไฟล์ในโฟลเดอร์

`cls_v6.pt` (โมเดล · strip optimizer แล้ว 3.2 MB) · `args.yaml` · `results.csv` / `results.png` · `confusion_matrix*.png` · `val_batch0_labels.jpg` / `val_batch0_pred.jpg`

## สิ่งที่ควรทำใน v7

- **ถ่ายเมล็ดเสียบนพื้นไม้เพิ่มเอง** — ยังเป็นข้อเดียวกับที่ v5 ค้างไว้ และ testsssss ก็แก้ไม่ได้ (คนละฉาก)
- หา dataset ที่มีหลายคลาสในภาพเดียว แทนชุดที่ถ่ายแยกกอง (ลดการจำฉาก)
- ทดลอง cap `beans-cls-tss/train` เหลือ ~700/คลาส ดูว่า ROBUSTA กลับมาเท่า v5 ได้โดยยังเก็บผลบน testsssss ไว้ไหม
- ตัดเมล็ดบนพื้นลายไม้: FastSAM (`Theeramet01/tesa-bean-grader` · `grader/pipeline.py`) ช้ากว่า Otsu ~100 เท่า ยังไม่วัดบน Pi 5
