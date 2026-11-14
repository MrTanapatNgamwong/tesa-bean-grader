# v5 · เพิ่มภาพมือถือบนพื้นไม้ (✅ ใช้งานอยู่)

- **วันที่:** 15 พ.ย. 2569
- **ข้อมูล:** `datasets/beans-cls-v5` = ROBUSTA + NIA + CFE (ชุดเดียวกับ v4) + **PHONE** (ใหม่)
- **ตั้งค่า:** YOLO26n-cls · 60 epochs · imgsz 320 · batch 16 · seed 0 (เหมือน v4 ทุกค่า ต่างกันแค่ข้อมูล · ค่าเต็มดู `args.yaml`) · เทรน ~96 นาที บน RTX 4060
- **เริ่มจาก:** `yolo26n-cls.pt`
- **บน Pi:** `cls_v5_ncnn_model`

## dataset ใหม่: PHONE (พื้นไม้)

- ภาพถ่ายมือถือ 123 ภาพ (4096×3072) บน**พื้นไม้** · ถ่าย 12 พ.ย. 2569 (ตามชื่อไฟล์) · ใกล้ภาพวันจริงที่สุดที่มี
- ต้นฉบับ: `phone/` (ภาพเต็ม แยกกอง good 71 · bad 50 · broken 2) · `phone_crops/` (เมล็ดที่ตัดแล้ว 2,272 ชิ้น: `raw/` มีพื้นไม้ · `masked/` ลบพื้น · `labels.csv` คลาส · `crops.csv` ตำแหน่งกรอบ)
- คลาสจาก `labels.csv`: ใช้ `final` ถ้ามี ไม่งั้นใช้ `draft` · ข้าม reject 82 ชิ้น → good 1,318 · husk 816 · full_black 33 · broken 15 · shell 7 · immature 1
- ใช้ `raw` (มีพื้นไม้) ไม่ใช้ `masked` เพราะตอนใช้งานจริงเมล็ดที่ตัดได้ยังมีพื้นหลังติดมา
- **ตรวจ husk 816 ชิ้น:** ให้ v4 ทายเทียบ (เห็นตรง 573 · ต่าง 243) แล้วดูด้วยตาครบทุกชิ้นที่ต่าง → ทั้งกองเป็นเมล็ดที่มีเปลือกผลแห้งสีน้ำตาลห่อ (= Hull/Husk แบบเดียวกับ NIA) ใช้ได้ทั้งหมด · v4 ทายผิดเพราะไม่เคยเห็นภาพแบบนี้

## สร้าง dataset + เทรน

```bat
python scripts\phone_to_cls.py --src D:/tesa-bean-grader-main/datasets/phone_crops --dst datasets/beans-cls-phone
python scripts\merge_cls.py
yolo classify train model=yolo26n-cls.pt data=datasets/beans-cls-v5 epochs=60 imgsz=320 device=0 name=cls_v5
yolo export model=runs\classify\cls_v5\weights\best.pt format=ncnn imgsz=320
```

(`beans-cls`, `beans-cls-nia`, `beans-cls-cfe` สร้างแบบเดียวกับ v4)

`merge_cls.py`: `KEEP_SPLIT = [beans-cls]` · `RESPLIT = [beans-cls-nia, beans-cls-cfe, beans-cls-phone]` · `DST = beans-cls-v5`
· PHONE แบ่งตามภาพถ่ายต้นฉบับ (เมล็ดจากภาพเดียวกันอยู่กองเดียวกัน) · NIA / CFE แบ่งเหมือน v4 ทุกภาพ

| ชุดรวม | train | val | test |
|---|---|---|---|
| broken | 5,517 | 619 | 524 |
| full_black | 10,800 | 908 | 1,190 |
| good | 8,952 | 1,132 | 922 |
| husk | 6,750 | 736 | 757 |
| immature | 918 | 32 | 35 |
| parchment | 403 | 7 | 7 |
| shell | 667 | 24 | 13 |

## ผล (test · วัดทั้งสองรุ่นด้วยภาพชุดเดียวกัน)

| test | v4 | v5 |
|---|---|---|
| **PHONE (พื้นไม้, 265 เม็ด)** | 0.581 | **0.925** |
| ROBUSTA (127) | 0.803 | **0.819** |
| NIA (290) | 0.955 | 0.955 |
| **ROBUSTA + NIA (417)** | 0.909 | **0.914 → ตัวเลขหลัก ~91%** |
| CFE (2,766) | 0.995 | 0.995 (สูงเกินจริง · กล้อง/ฉากเดียวกับ train) |
| top1 val (ชุด v5) | — | 0.979 (epoch 54) |

**บน Pi (NCNN):** PHONE 246/265 = 0.928 · ROBUSTA + NIA + PHONE 627/682 = **0.919** · ต่างจากบนคอม 1 เม็ด (husk ที่ความมั่นใจก้ำกึ่ง) · ~14–18 ms/เม็ด (รวมเวลาเปิดไฟล์)

```bat
python scripts\eval_cls.py --model runs\classify\cls_v5\weights\best.pt --data datasets\beans-cls\test
python scripts\eval_cls.py --model runs\classify\cls_v5\weights\best.pt --data datasets\beans-cls-v5\test --include nia_
python scripts\eval_cls.py --model runs\classify\cls_v5\weights\best.pt --data datasets\beans-cls-v5\test --include cfe_
python scripts\eval_cls.py --model runs\classify\cls_v5\weights\best.pt --data datasets\beans-cls-v5\test --include phone_
```

### ความแม่นต่อคลาส · PHONE test

| คลาส | จำนวน | v4 | v5 |
|---|---|---|---|
| good | 104 | 0.33 | **0.98** |
| husk | 149 | 0.78 | **0.95** |
| full_black | 8 | 0.50 | 0.25 |
| shell | 3 | 0.00 | 0.00 |
| broken | 1 | 0.00 | 0.00 |

### ความแม่นต่อคลาส · ROBUSTA test

| คลาส | v4 | v5 |
|---|---|---|
| full_black | 1.00 | 1.00 |
| husk | 0.96 | 1.00 |
| immature | 0.82 | 0.73 |
| parchment | 0.71 | 0.71 |
| good | 0.69 | 0.69 |
| broken | 0.54 | 0.67 |
| shell | 0.50 | 0.40 |

## ข้อสังเกต

- **v4 พังกับภาพพื้นไม้:** ทายเมล็ดดีผิดเป็น husk / broken / immature 2 ใน 3 → v5 แก้ได้ (good 0.98, husk 0.95)
- ⚠️ **เมล็ดเสียบนพื้นไม้ถูกทายเป็น husk:** full_black → husk 6/8 · shell / broken ก็เป็น husk · เพราะเมล็ดเสียบนพื้นไม้ที่เคยเห็นเกือบทั้งหมดเป็น husk → วันจริงบนพื้นไม้ husk อาจสูงเกินจริง ส่วน full_black / shell / broken ต่ำเกินจริง (test คลาสเหล่านี้มี 1–8 เม็ด ตัวเลขยังไม่แน่นอน)
- ROBUSTA ต่อคลาสขยับ 1–3 เม็ด อยู่ในระดับที่ขยับเองได้
- `detect.py` ยังตัดเมล็ดด้วย OpenCV ซึ่งใช้ได้แค่พื้นสีอ่อน → ภาพเต็มบนพื้นไม้ต้องใช้โมเดลตรวจจับ (Day 2) · `phone_crops/crops.csv` มีกรอบเมล็ดบนพื้นไม้ ใช้เทรนตัวตรวจจับได้

## ไฟล์ในโฟลเดอร์

`cls_v5.pt` (โมเดล) · `args.yaml` · `results.csv` / `results.png` · `confusion_matrix*.png` · `val_batch0_labels.jpg` / `val_batch0_pred.jpg`

## สิ่งที่ควรทำใน v6

- ถ่ายเมล็ดเสียชนิดอื่นบนพื้นไม้เพิ่ม: full_black, broken, shell, immature, parchment
- หาข้อมูล shell / parchment / immature เพิ่ม (ยังมาจาก ROBUSTA ชุดเดียวเป็นหลัก)
- วันจริง: ผสมข้อมูลผู้จัด
