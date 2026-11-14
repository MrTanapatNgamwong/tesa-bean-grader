# v4 · เพิ่ม dataset ที่ 3 (✅ ใช้งานอยู่)

- **วันที่:** 14 พ.ย. 2569
- **ข้อมูล:** `datasets/beans-cls-v4` = ROBUSTA + NIA (ชุดเดียวกับ v3) + **OPTIMIZED GREEN CFE BEANS** (ใหม่)
- **ตั้งค่า:** YOLO26n-cls · 60 epochs · imgsz 320 · batch 16 · seed 0 (เหมือน v3 ทุกค่า ต่างกันแค่ข้อมูล · ค่าเต็มดู `args.yaml`) · เทรน ~84 นาที บน RTX 4060
- **เริ่มจาก:** `yolo26n-cls.pt` (ไม่ได้ต่อยอดจาก v3)
- **บน Pi:** `cls_v4_ncnn_model` · ~12 ms/เม็ด

## dataset ใหม่: OPTIMIZED GREEN CFE BEANS

- Roboflow · `green-coffee-beans/optimized-green-cfe-beans` v2 · CC BY 4.0 · https://universe.roboflow.com/green-coffee-beans/optimized-green-cfe-beans
- 4,992 ภาพ 416×416 · พื้นขาว ถ่ายมือถือ · 1 คลาสต่อภาพ · ดูเป็นเมล็ดอาราบิก้า
- แปลงคลาส (preset `cfe`): `normal → good` · `black → full_black` · `broken → broken` · `cherry → husk`
  - `cherry` ปนกันระหว่างผลแห้งทั้งผล (หน้าตาเหมือน husk ของ NIA ที่อยู่ใน v3 แล้ว) กับเปลือกแห้งเป็นโพรง (= hull/husk) · โจทย์ไม่มีคลาส dried cherry → ใส่ husk
- ไม่มี shell / parchment / immature

**สิ่งที่ต้องแก้ใน `crop_beans.py` ก่อนใช้ชุดนี้**

- label ~14% เป็น polygon → เพิ่มการแปลง polygon เป็นกรอบ (ตัวเดิมอ่านแค่ 5 ตัวเลขแรก ตัดผิดตำแหน่งโดยไม่เตือน)
- เมล็ดริมภาพถูกตัดไม่เต็มเม็ด → เพิ่ม `--skip-edge` (ตัดทิ้ง ~30%)
- สำเนาภาพเดียวกันกระจายหลาย split (747 จาก 2,040 ภาพต้นฉบับ) · test มีแค่ 12 ภาพ → ใส่ใน `RESPLIT`

**ไม่ใช้:** `green-coffee-bean` (Cor Jesu College) เพราะภาพเป็นขาวดำ, คลาสเป็นระดับคุณภาพ (Good/Medium/Low) ไม่ใช่ชนิดตำหนิ และตัดมาจากวิดีโอ

## สร้าง dataset + เทรน

```bat
python scripts\crop_beans.py
python scripts\crop_beans.py --preset nia --src datasets/coffee-defect-nia --dst datasets/beans-cls-nia --prefix nia
python scripts\crop_beans.py --preset cfe --src datasets/green-cfe-bean --dst datasets/beans-cls-cfe --prefix cfe --skip-edge
python scripts\merge_cls.py
yolo classify train model=yolo26n-cls.pt data=datasets/beans-cls-v4 epochs=60 imgsz=320 device=0 name=cls_v4
yolo export model=runs\classify\cls_v4\weights\best.pt format=ncnn imgsz=320
```

`merge_cls.py`: `KEEP_SPLIT = [beans-cls]` · `RESPLIT = [beans-cls-nia, beans-cls-cfe]` · `DST = beans-cls-v4`

| ชุดรวม | train | val | test |
|---|---|---|---|
| broken | 5,506 | 616 | 523 |
| full_black | 10,779 | 904 | 1,182 |
| good | 7,856 | 1,014 | 818 |
| husk | 6,188 | 631 | 608 |
| immature | 917 | 32 | 35 |
| parchment | 403 | 7 | 7 |
| shell | 664 | 23 | 10 |

ROBUSTA/NIA ใน test เป็นภาพชุดเดียวกับ v3 → เทียบกันได้ตรง

## ผล (test · วัดทั้งสองรุ่นด้วยภาพชุดเดียวกัน)

| test | v3 | v4 |
|---|---|---|
| ROBUSTA (127 เม็ด) | 0.787 | **0.803** |
| NIA (290 เม็ด) | 0.959 | 0.955 |
| **ROBUSTA + NIA (417 เม็ด)** | 0.909 | **0.909 → ตัวเลขหลัก ~91%** |
| CFE (2,766 เม็ด) | 0.410 | 0.995 (สูงเกินจริง · กล้อง/ฉากเดียวกับ train) |
| top1 val (ชุด v4) | — | 0.980 (epoch 36) |

v3 ROBUSTA + NIA = (100 + 278) / 417 = 0.906 · v4 = (102 + 277) / 417 = 0.909

**บน Pi (NCNN):** ROBUSTA + NIA 379/417 = 0.909 · CFE 2751/2766 · **ตรงกับบนคอมทุกเม็ด** · ~12 ms/เม็ด

```bat
python scripts\eval_cls.py --model runs\classify\cls_v4\weights\best.pt --data datasets\beans-cls\test
python scripts\eval_cls.py --model runs\classify\cls_v4\weights\best.pt --data datasets\beans-cls-v4\test --include nia_
python scripts\eval_cls.py --model runs\classify\cls_v4\weights\best.pt --data datasets\beans-cls-v4\test --include cfe_
```

### ความแม่นต่อคลาส · ROBUSTA test

| คลาส | v3 | v4 |
|---|---|---|
| full_black | 0.97 | 1.00 |
| husk | 1.00 | 0.96 |
| immature | 0.73 | 0.82 |
| parchment | 0.71 | 0.71 |
| good | 0.46 | 0.69 |
| broken | 0.67 | 0.54 |
| shell | 0.40 | 0.50 |

## ข้อสังเกต

- **v3 พังกับภาพแบบใหม่:** บน CFE ทายเมล็ดดีเป็น immature 551/773 → การเพิ่มข้อมูลหลายแหล่งคือทางแก้ domain shift
- ดีขึ้น: good, immature, shell, full_black (ROBUSTA)
- ต้องจับตา: broken ROBUSTA 0.67 → 0.54 (broken→parchment 7) · immature NIA 1.00 → 0.83 · test แต่ละคลาสมี 10–40 เม็ด ผิด 1 เม็ด = 3–10% จึงยังสรุปไม่ได้
- จำนวนต่อคลาสเอียงมาก (full_black 10,779 vs parchment 403) · broken ของ CFE บางชิ้นหน้าตาเหมือน shell

## ไฟล์ในโฟลเดอร์

`cls_v4.pt` (โมเดล) · `args.yaml` · `results.csv` / `results.png` · `confusion_matrix*.png` · `val_batch0_labels.jpg` / `val_batch0_pred.jpg`

## สิ่งที่ควรทำใน v5

- หาข้อมูล shell / parchment / immature เพิ่ม (ตอนนี้มีจาก ROBUSTA ชุดเดียว)
- ลองเปลี่ยน `dried-cherry-pod` ของ ROBUSTA เป็น husk ให้สอดคล้องกับ CFE / NIA
- วันจริง: ผสมข้อมูลผู้จัด
