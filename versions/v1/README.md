# v1 · classifier รอบแรก (เลิกใช้)

- **วันที่:** 10 พ.ย. 2569
- **ข้อมูล:** `datasets/beans-cls` · เมล็ดที่ `crop_beans.py` ตัดจาก ROBUSTA DATASET · train 8,306 / val 229 / test 127 เม็ด
- **ตั้งค่า:** YOLO26n-cls · 30 epochs · imgsz 224
- **ผล:** top1 val **0.865** · 0.5 ms/เม็ด บน RTX 4060
- **ไฟล์ในโฟลเดอร์:** `confusion_matrix_normalized.png` เท่านั้น · ไฟล์โมเดลถูกลบไปแล้ว (เทรนใหม่ได้จากคำสั่งด้านล่าง)

```bat
yolo classify train model=yolo26n-cls.pt data=datasets/beans-cls epochs=30 imgsz=224 device=0 name=cls_v1
```

## ความแม่นต่อคลาส (val)

| คลาส | v1 |
|---|---|
| husk | 1.00 |
| full_black | 0.93 |
| good | 0.88 |
| broken | 0.84 |
| immature | 0.78 |
| parchment | 0.57 |
| shell | 0.57 |

**ข้อสังเกต:** shell อ่อนสุด (ผิดเป็น broken 22%, immature 17%) · parchment ใน val มีแค่ 7 เม็ด ตัวเลขจึงแกว่งง่าย

**ทำไมไปต่อ v2:** ลองเพิ่ม epochs และขนาดภาพ เพื่อดูว่าช่วยคลาสที่อ่อนไหม
