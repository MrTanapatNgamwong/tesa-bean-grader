# Datasets

## 1. ROBUSTA DATASET (No digkit3) · ใช้เทรน (cls_v2–v5)

- Roboflow Universe · Renies Workspace · CC BY 4.0 · โรบัสต้าดิบ · กล้อง DSLR พื้นขาว
- 3,219 ภาพ (ต้นฉบับ 438 · train ถูก augment 10 เท่า) · label แบบกรอบ · 16 คลาส มีครบ 7 คลาสของโจทย์

| คลาสโจทย์ | ชื่อใน dataset | train | val | test |
|---|---|---|---|---|
| good | good | 715 | 26 | 13 |
| shell | shell | 664 | 23 | 10 |
| full_black | full-black | 2,234 | 56 | 35 |
| hull_husk | husk | 1,999 | 55 | 27 |
| broken | broken-chipped-cut | 1,540 | 44 | 24 |
| parchment | parchment | 403 | 7 | 7 |
| immature | immature | 751 | 18 | 11 |

(จำนวนเมล็ดหลังตัดด้วย crop_beans.py)

**ข้อจำกัด:** เมล็ด ~28% ไม่มี label (ประมาณจาก OpenCV) → ไม่เทรน detection ตรง · เมล็ดดีมีแค่ ~11% · Parchment ใน val/test มีน้อย

## 2. coffee-bean-defect (niacubilla) · ใช้เทรนร่วมใน cls_v3–v5

- Roboflow Universe · CC BY 4.0 · 2,520 ภาพ · 640×640 · พื้นผ้าขาว ถ่ายมือถือ · 1–6 ชิ้น/ภาพ
- 9 คลาส: green, black, broken, husk, fraghusk, immature, foreign, infested, sour
- เมล็ดดี (green) มีแค่ 6% · ส่วนใหญ่เป็นสิ่งแปลกปลอมและเมล็ดเสีย
- ผลกับ cls_v2 (ไม่เคยเห็น NIA): ตัดเมล็ดตรง 52/52 แต่ทายเมล็ดดีถูก 9/52 → domain shift
- ข้อมูลรั่ว: ภาพต้นฉบับทุกภาพมี 2 สำเนาอยู่คนละ split → `merge_cls.py` เทรวมแล้วแบ่งใหม่ 80/10/10 ตามภาพต้นฉบับ

## 3. OPTIMIZED GREEN CFE BEANS (green-coffee-beans) · ใช้เทรนร่วมใน cls_v4–v5

- Roboflow Universe · `green-coffee-beans/optimized-green-cfe-beans` v2 · CC BY 4.0 · 4,992 ภาพ 416×416 · พื้นขาว ถ่ายมือถือ · 1 คลาสต่อภาพ
- 4 คลาส: normal → good · black → full_black · broken → broken · cherry → husk (preset `cfe`)
- label ~14% เป็น polygon · เมล็ดริมภาพถูกตัด → ใช้ `--skip-edge` · สำเนาภาพรั่วข้าม split → แบ่งใหม่ใน `merge_cls.py`
- รายละเอียด: [versions/v4](../versions/v4/README.md)

## 4. Green Coffee Bean (Cor Jesu College) · ไม่ใช้

- Roboflow Universe · `cor-jesu-college-lvftr/green-coffee-bean` v1 · CC BY 4.0
- ภาพขาวดำ (Grayscale + adaptive equalization) · คลาสเป็นระดับคุณภาพ Good / Medium / Low · label เป็น polygon · ตัดจากวิดีโอ
- ไม่ใช้เพราะคลาสแปลงเป็น 7 คลาสไม่ได้ และภาพไม่มีสี (หลายคลาสของเราแยกด้วยสี)

## 5. PHONE (ภาพมือถือบนพื้นไม้) · ใช้เทรนร่วมใน cls_v5

- ภาพถ่ายมือถือ 123 ภาพ (4096×3072) บนพื้นไม้ · `phone/` ภาพเต็ม · `phone_crops/` เมล็ดที่ตัดแล้ว 2,272 ชิ้น + `labels.csv` + `crops.csv`
- `phone_to_cls.py` → `datasets/beans-cls-phone` (ใช้ `raw` ที่มีพื้นไม้ · ข้าม reject) · ไฟล์ขึ้นต้น `phone_`
- good 1,318 · husk 816 · full_black 33 · broken 15 · shell 7 · immature 1
- รายละเอียด: [versions/v5](../versions/v5/README.md)

## 6. testsssss (rt-pee) · ใช้เทรนร่วมใน cls_v6

- Roboflow Universe · `rt-pee/testsssss-jhgg2` v1 · CC BY 4.0 · YOLOv8 detection (กรอบ)
- 263 ภาพ (train 184 / valid 53 / test 26) · 512×512 **ยืด** จากภาพแนวตั้ง · พื้นขาวเทา · 15–107 เมล็ด/ภาพ
- 6 คลาส: black, broken, immature, normal, parchment, shell · **ไม่มี husk** (preset `tss`)
- ได้มาจาก `Theeramet01/tesa-bean-grader` (`HANDOFF.md`) · เพิ่มเพื่ออุด shell / parchment / immature ที่ v5 ขาด
- **ตรวจข้อมูลรั่วแล้ว:** 263 ภาพ = 263 ต้นฉบับไม่ซ้ำ · md5 ซ้ำข้าม split = 0 · ซ้ำชื่อต้นฉบับข้าม split = 0 → **ใช้ `KEEP_SPLIT`** (ต่างจาก NIA / CFE)

| คลาสโจทย์ | ชื่อใน dataset | train | val | test |
|---|---|---|---|---|
| good | normal | 258 | 92 | 30 |
| shell | shell | 2,020 | 571 | 280 |
| full_black | black | 834 | 238 | 120 |
| broken | broken | 2,203 | 524 | 277 |
| parchment | parchment | 719 | 205 | 103 |
| immature | immature | 1,743 | 538 | 236 |

(จำนวนเมล็ดหลังตัดด้วย `crop_beans.py --preset tss` · ไฟล์ขึ้นต้น `tss_`)

**ข้อจำกัด:** ทุกภาพมีคลาสเดียว (ถ่ายเป็นกองแยกชนิด) → โมเดลอาจจำแสง/ฉากแทนเมล็ด · เมล็ดเล็ก ~17×22 px → `--min-size 16` ทิ้งไปราว 1/3 และเบลอเมื่อขยายเป็น 320 → **ห้ามใช้ tss test เป็นตัวเลขหลัก**

## 7. ชุดที่ใช้เทรนจริง

- **beans-cls-v3** (cls_v3): ROBUSTA + NIA
- **beans-cls-v4** (cls_v4): ROBUSTA + NIA + CFE · `crop_beans.py` ทีละชุด → `merge_cls.py` (ROBUSTA ใช้การแบ่งเดิม · NIA + CFE แบ่งใหม่ 80/10/10 ตามภาพต้นฉบับ)
- **beans-cls-v5** (cls_v5): ROBUSTA + NIA + CFE + PHONE · PHONE แบ่งตามภาพถ่ายต้นฉบับ
- **beans-cls-v6** (cls_v6): ROBUSTA + NIA + CFE + PHONE + **testsssss** · testsssss ใช้การแบ่งเดิมของ Roboflow (ตรวจแล้วว่าไม่รั่ว)
- ไฟล์จาก NIA ขึ้นต้น `nia_` · CFE ขึ้นต้น `cfe_` · PHONE ขึ้นต้น `phone_` · testsssss ขึ้นต้น `tss_` (ใช้แยกวัดผลด้วย `eval_cls.py --include`)
