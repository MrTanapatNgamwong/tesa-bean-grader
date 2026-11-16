# เส้นทางการพัฒนา (9–14 พ.ย. 2026)

| # | ขั้น | ผล | ปัญหาที่เจอ → วิธีแก้ |
|---|---|---|---|
| 1 | ทำความเข้าใจโจทย์ | วางแนว: เทรนบนคอม → export NCNN → รันบน Pi · เตรียม pipeline ไม่ใช่โมเดลสำเร็จรูป | — |
| 2 | ลง Raspberry Pi OS | SSH ได้ | host key เก่า → `ssh-keygen -R tesa-pi.local` |
| 3 | อัปเดต + Wi-Fi | ต่อได้ทั้งบ้านและ hotspot | สลับ Wi-Fi ระหว่างอัปเดตทำ SSH หลุด → `nmcli connection add` (เพิ่มโปรไฟล์ไม่สลับทันที) |
| 4 | venv คอม | Python 3.13 + PyTorch CUDA | venv แรกได้ 3.10 → ลบแล้วสร้างด้วย `py -3.13` |
| 5 | Milestone: coco8-seg | เทรน GPU → NCNN → Pi: 122 ms/ภาพ · RAM 0.87 GB | pip โหลด pnnx ช้า → ติดตั้งเอง · `/usr/bin/time` ไม่มี → `apt install time` |
| 6 | หา dataset | เลือก ROBUSTA DATASET (7 คลาสครบ ชื่อตรงโจทย์) | label ตกหล่น ~28% → ตัดเมล็ดตามกรอบที่มี แทนเทรน detection ตรง |
| 7 | crop_beans.py | เมล็ดเดี่ยว 8,306 / 229 / 127 | `import yaml` ไม่มี → `pip install pyyaml` |
| 8 | classifier v1 / v2 | top1 0.865 ทั้งคู่ · v2 แม่น full_black 0.96 → ใช้ v2 | ปรับ epochs/imgsz ไม่ช่วยภาพรวม · shell↔broken ยังสับสน |
| 9 | classifier บน Pi | 11.7 ms/เม็ด · NCNN = PyTorch (0.795) | ชื่อโฟลเดอร์ต้อง `_ncnn_model` · ลืมเข้า venv |
| 10 | pipeline (ตัด → classify → นับ) | ภาพ → JSON + ภาพวาดกรอบ ครบสาย | — |
| 11 | ทดสอบ dataset อื่น | ตัดเมล็ดตรง 52/52 แต่ classify เมล็ดดีถูกแค่ 9/52 | domain shift → ต้องเทรนด้วยข้อมูลหลายแบบ / ข้อมูลผู้จัด |
| 12 | classifier v3 (ROBUSTA + NIA) | test ROBUSTA 0.787 · NIA 0.959 (v2 0.693) → ใช้ v3 | NIA ทุกภาพมี 2 สำเนาคนละ split (ข้อมูลรั่ว) → `merge_cls.py` แบ่งใหม่ตามภาพต้นฉบับ |
| 13 | ปรับขอบเขต | Pi ทำแค่ตรวจจับ + นับ · เกรดและหน้าเว็บย้ายไป server | ตัด grade.py / app.py ออก · MQTT จะออกแบบใหม่ |
| 14 | classifier v4 (+ CFE) | ROBUSTA + NIA 0.909 · CFE 0.995 (v3 0.410) → ใช้ v4 | label บางส่วนเป็น polygon → แก้ `crop_beans.py` · เมล็ดริมภาพถูกตัด → `--skip-edge` · ชุด Cor Jesu เป็นภาพขาวดำ + คลาสเป็นระดับคุณภาพ → ไม่ใช้ |
| 15 | classifier v5 (+ PHONE พื้นไม้) | PHONE 0.581 → 0.925 · ROBUSTA + NIA 0.914 → ใช้ v5 | husk 816 ชิ้นเป็นคลาสที่ระบบเดา → ให้ v4 ทายเทียบ + ดูด้วยตาครบ ยืนยันว่าเป็น husk · เมล็ดเสียบนพื้นไม้ถูกทายเป็น husk → ต้องถ่ายเมล็ดเสียชนิดอื่นบนพื้นไม้เพิ่ม |
| 16 | classifier v6 (+ testsssss) | testsssss 0.251 → 0.890 · PHONE 0.925 → 0.943 · ROBUSTA+NIA 0.914 → 0.909 → ใช้ v6 | HANDOFF จากเพื่อนชี้ dataset ที่มี shell/parchment/immature เยอะ · ตรวจข้อมูลรั่วเองก่อนเชื่อ (NIA/CFE เคยรั่ว) พบว่าไม่รั่ว → ใช้ KEEP_SPLIT · เทรนถูกหยุดกลางทางที่ epoch 35 → resume จาก last.pt ไม่ต้องเริ่มใหม่ · ข้อมูลใหม่ช่วยเฉพาะโดเมนตัวเอง (ROBUSTA ทั้ง 3 คลาสไม่ขึ้น) เพราะ testsssss ทุกภาพมีคลาสเดียว |

## บทเรียน

- ดูหน้าบรรทัดก่อนพิมพ์: `C:\...>` = คอม · `admin@tesa-pi` = Pi · `(.venv)` = อยู่ใน venv
- งานนานบน Pi รันใน tmux
- คำสั่งที่มี `| grep` อาจซ่อน error
- ตัวเลขบน val กับ test ต่างกันได้มากเมื่อข้อมูลน้อย ต้องเทียบชุดเดียวกัน
- โมเดลเก่งบนข้อมูลแบบที่เทรน ไม่ได้แปลว่าเก่งกับภาพแบบอื่น
