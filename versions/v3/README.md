# v3 · รวม 2 dataset (✅ ใช้งานอยู่)

- **วันที่:** 12 พ.ย. 2569
- **ข้อมูล:** `datasets/beans-cls-v3` = ROBUSTA + NIA (coffee-bean-defect, niacubilla)
- **ตั้งค่า:** YOLO26n-cls · 60 epochs · imgsz 320 · batch 16 · seed 0 (ค่าเต็มดู `args.yaml`) · เทรน ~24 นาที บน RTX 4060
- **บน Pi:** export เป็น NCNN แล้วตั้งชื่อ `cls_v3_ncnn_model` · ~5–12 ms/เม็ด · ใช้โดย `detector/detect.py`

## สร้าง dataset + เทรน

```bat
python scripts\crop_beans.py
python scripts\crop_beans.py --preset nia --src datasets/coffee-defect-nia --dst datasets/beans-cls-nia --prefix nia
python scripts\merge_cls.py
yolo classify train model=yolo26n-cls.pt data=datasets/beans-cls-v3 epochs=60 imgsz=320 device=0 name=cls_v3
yolo export model=runs\classify\cls_v3\weights\best.pt format=ncnn imgsz=320
```

- `merge_cls.py`: ROBUSTA ใช้การแบ่งเดิม · NIA เทรวมแล้วแบ่งใหม่ 80/10/10 **ตามภาพต้นฉบับ** เพราะชุดเดิมมีภาพเดียวกัน 2 สำเนาอยู่คนละ split (ข้อมูลรั่ว ทำให้ผล test ดีเกินจริง)
- ไฟล์จาก NIA ขึ้นต้นด้วย `nia_` ใช้แยกวัดผลได้

## ผล

| การทดสอบ | v2 | v3 |
|---|---|---|
| top1 test ROBUSTA | 0.795 | **0.787** |
| top1 test NIA | 0.693 | **0.959** |
| top1 val (ชุด v3 · ROBUSTA + NIA) | — | 0.924 (epoch 58) |

```bat
python scripts\eval_cls.py --model runs\classify\cls_v3\weights\best.pt --data datasets\beans-cls-v3\test --exclude nia_
python scripts\eval_cls.py --model runs\classify\cls_v3\weights\best.pt --data datasets\beans-cls-v3\test --include nia_
```

**สรุป:** ROBUSTA ลดเล็กน้อย แต่ภาพแบบ NIA ดีขึ้นมาก → ทนต่อภาพคนละแบบมากขึ้น · ยังสับสน **good ↔ full_black** และ **shell ↔ broken**

## ไฟล์ในโฟลเดอร์

| ไฟล์ | คืออะไร |
|---|---|
| `cls_v3.pt` | โมเดล (= `runs\classify\cls_v3\weights\best.pt`) |
| `args.yaml` | ค่าทั้งหมดที่ใช้เทรน · ใช้เทรนซ้ำให้ได้ผลเหมือนเดิม |
| `results.csv` / `results.png` | loss + ความแม่นทุก epoch |
| `confusion_matrix.png` / `confusion_matrix_normalized.png` | คลาสจริง vs ที่ทาย (จำนวน / สัดส่วน) บน val |
| `val_batch0_labels.jpg` / `val_batch0_pred.jpg` | ตัวอย่างภาพ val: คลาสจริง vs ที่โมเดลทาย |

## ข้อจำกัด / สิ่งที่ควรทำใน v4

- วันจริงผู้จัดให้ภาพแบบใหม่ → เทรน v4 โดยผสมข้อมูลผู้จัด
- เพิ่มข้อมูลคลาสที่สับสน (good, full_black, shell, broken)
