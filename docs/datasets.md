# Datasets

## 1. ROBUSTA DATASET (No digkit3) · ใช้เทรน

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

## 2. coffee-bean-defect (niacubilla) · ใช้ทดสอบ

- Roboflow Universe · CC BY 4.0 · 2,520 ภาพ · 640×640 · พื้นผ้าขาว ถ่ายมือถือ · 1–6 ชิ้น/ภาพ
- 9 คลาส: green, black, broken, husk, fraghusk, immature, foreign, infested, sour
- เมล็ดดี (green) มีแค่ 6% · ส่วนใหญ่เป็นสิ่งแปลกปลอมและเมล็ดเสีย
- ผล: ตัดเมล็ดตรง 52/52 แต่โมเดลทายเมล็ดดีถูก 9/52 → domain shift
