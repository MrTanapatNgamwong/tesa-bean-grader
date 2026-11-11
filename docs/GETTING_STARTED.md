# 🚀 คู่มือเริ่มต้นใช้งาน Bean Grader (ตั้งแต่ศูนย์)

คู่มือนี้พาทำตั้งแต่ยังไม่มีอะไรในเครื่อง จนได้หน้าเว็บตรวจเกรดเมล็ดกาแฟบน Raspberry Pi และส่งผลผ่าน MQTT ทำตามลำดับทีละขั้น ไม่ต้องข้าม

> **อ่านก่อน:** ทุกคำสั่งในคู่มือบอกไว้ว่ารันที่ไหน
> - 💻 **คอม** = เครื่อง Windows (หน้าบรรทัด `C:\...>`)
> - 🍓 **Pi** = Raspberry Pi ผ่าน SSH (หน้าบรรทัด `admin@tesa-pi:~ $`)
> - ถ้าหน้าบรรทัดมี `(.venv)` = อยู่ใน virtual environment แล้ว

---

## สารบัญ

0. [ภาพรวม: ระบบทำงานยังไง](#0-ภาพรวม-ระบบทำงานยังไง)
1. [สิ่งที่ต้องมี](#1-สิ่งที่ต้องมี)
2. [เตรียมคอม (เครื่องเทรน)](#2-เตรียมคอม-เครื่องเทรน)
3. [ดาวน์โหลดโค้ดและข้อมูล](#3-ดาวน์โหลดโค้ดและข้อมูล)
4. [เตรียมข้อมูลและเทรนโมเดล](#4-เตรียมข้อมูลและเทรนโมเดล)
5. [เตรียม Raspberry Pi](#5-เตรียม-raspberry-pi)
6. [ส่งโมเดลและโค้ดไป Pi](#6-ส่งโมเดลและโค้ดไป-pi)
7. [ทดสอบบน Pi](#7-ทดสอบบน-pi)
8. [เปิดหน้าเว็บ Bean Grader](#8-เปิดหน้าเว็บ-bean-grader)
9. [ส่งผลผ่าน MQTT](#9-ส่งผลผ่าน-mqtt)
10. [ปรับแต่ง: เกณฑ์เกรด / คลาส / server](#10-ปรับแต่ง)
11. [แก้ปัญหาที่พบบ่อย](#11-แก้ปัญหาที่พบบ่อย)
12. [คำศัพท์](#12-คำศัพท์)

---

## 0. ภาพรวม: ระบบทำงานยังไง

```
 คอม (มีการ์ดจอ NVIDIA)                     Raspberry Pi 5
┌──────────────────────────┐            ┌─────────────────────────────────┐
│ dataset → ตัดเมล็ด        │   export   │ ภาพ → ตัดเมล็ด (OpenCV)          │
│ → เทรน classifier (GPU)  │ ─────────► │ → จำแนก 7 คลาส (NCNN)            │
│ → ได้โมเดล .pt           │   NCNN     │ → นับ → เกรด A/B/C → หน้าเว็บ     │
└──────────────────────────┘            │ → ส่ง JSON ผ่าน MQTT ไป server    │
                                        └─────────────────────────────────┘
```

- **คอม** ใช้เทรน (เร็วเพราะมี GPU) · **Pi** ใช้รันจริง (ไม่มี GPU ใช้ CPU ล้วน)
- โมเดลเทรนเป็น `.pt` (PyTorch) แล้วแปลงเป็น **NCNN** เพื่อให้รันบน Pi ได้เร็วและเบา

**มีโมเดลแล้วไม่อยากเทรนเอง?** repo นี้มี `models/cls_v2.pt` ให้แล้ว ข้ามข้อ 4 ไปข้อ 5 ได้ (แต่ยังต้องทำข้อ 2 เพื่อ export)

---

## 1. สิ่งที่ต้องมี

| อุปกรณ์ | หมายเหตุ |
|---|---|
| คอม Windows + การ์ดจอ NVIDIA | ใช้เทรน · ไม่มีการ์ดจอใช้ Google Colab แทนได้ (ช้ากว่า) |
| Raspberry Pi 5 (RAM 4 GB ขึ้นไป) | ทดสอบจริงกับรุ่น 16 GB |
| microSD 32 GB + card reader | ลง OS ของ Pi |
| อะแดปเตอร์ 27W USB-C + พัดลม/Active Cooler | Pi 5 กินไฟและร้อนตอนรันโมเดล |
| Wi-Fi ที่คอมกับ Pi ต่อวงเดียวกันได้ | หรือ hotspot มือถือ |

ความรู้ที่ช่วยได้: พิมพ์คำสั่งใน Command Prompt/Terminal ได้, Python เบื้องต้น

---

## 2. เตรียมคอม (เครื่องเทรน)

### 2.1 ติดตั้งโปรแกรม 💻

1. **Python 3.13** จาก python.org → ตอนติดตั้ง **ติ๊ก "Add python.exe to PATH"**
2. **Git** จาก git-scm.com (กด Next ได้หมด)
3. **VS Code** จาก code.visualstudio.com + extension **Python** ของ Microsoft (ไม่บังคับ แต่ช่วยมาก)
4. **ไดรเวอร์การ์ดจอ NVIDIA** ล่าสุด

เช็ก: เปิด Command Prompt ใหม่ แล้วพิมพ์

```bat
python --version
git --version
nvidia-smi
```

`nvidia-smi` ต้องเห็นชื่อการ์ดจอ และ `CUDA Version` มุมขวาบน

> มี Python หลายเวอร์ชันในเครื่อง? ใช้ `py -0` ดูรายการ แล้วใช้ `py -3.13` แทน `python` ตอนสร้าง venv

### 2.2 สร้าง virtual environment (venv) 💻

**venv** = กล่องแยกไลบรารีของโปรเจกต์นี้ ไม่ให้ตีกับโปรเจกต์อื่น

```bat
mkdir C:\tesa-pi
cd C:\tesa-pi
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
```

ทุกครั้งที่เปิด Command Prompt ใหม่ ต้องรัน `cd C:\tesa-pi` และ `.venv\Scripts\activate` ก่อนเสมอ

### 2.3 ติดตั้ง PyTorch แบบใช้ GPU 💻 `(.venv)`

ไปที่ **pytorch.org → Get Started** เลือก Stable / Windows / Pip / Python / CUDA เวอร์ชันสูงสุดที่ไม่เกิน `CUDA Version` จาก `nvidia-smi` แล้วก๊อปคำสั่งมารัน เช่น

```bat
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu134
```

> ⚠️ อย่าใช้ `pip install torch` เฉย ๆ บน Windows จะได้ตัวที่ใช้แค่ CPU เทรนช้ามากโดยไม่มีอะไรเตือน

เช็กว่าเห็น GPU:

```bat
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

ต้องได้ `True` และชื่อการ์ดจอ

### 2.4 ติดตั้งไลบรารีที่เหลือ 💻 `(.venv)`

```bat
pip install ultralytics opencv-python matplotlib pyyaml pnnx
yolo checks
```

- `ultralytics` เทรน/export YOLO · `opencv-python` ประมวลผลภาพ · `pyyaml` อ่านไฟล์ตั้งค่า · `pnnx` ใช้ตอนแปลงเป็น NCNN

---

## 3. ดาวน์โหลดโค้ดและข้อมูล

### 3.1 โค้ด 💻

```bat
cd C:\
git clone https://github.com/MrTanapatNgamwong/tesa-bean-grader.git
```

repo เป็น Private ต้องได้รับเชิญเป็น collaborator ก่อน แล้วคัดลอกโค้ดไปที่ทำงาน:

```bat
xcopy /E /I C:\tesa-bean-grader\grader C:\tesa-pi\grader
xcopy /E /I C:\tesa-bean-grader\scripts C:\tesa-pi\scripts
xcopy /E /I C:\tesa-bean-grader\models C:\tesa-pi\models
```

### 3.2 Dataset 💻

1. เปิด Roboflow Universe → **ROBUSTA DATASET | No digkit3** (Renies Workspace)
2. Download Dataset → format **YOLOv8** (หรือ YOLO26) → Download zip to computer
3. แตกไฟล์ไปที่ `C:\tesa-pi\datasets\robusta-digkit3`

```bat
cd C:\tesa-pi
mkdir datasets\robusta-digkit3
tar -xf "%USERPROFILE%\Downloads\ชื่อไฟล์.zip" -C datasets\robusta-digkit3
dir datasets\robusta-digkit3
```

ต้องเห็น `data.yaml`, `train`, `valid`, `test` · รายละเอียด dataset: [datasets.md](datasets.md)

---

## 4. เตรียมข้อมูลและเทรนโมเดล

> ข้ามได้ถ้าใช้ `models/cls_v2.pt` ที่มีให้

### 4.1 ตัดเมล็ดเป็นภาพเดี่ยว 💻 `(.venv)`

dataset ให้ภาพที่มีหลายเมล็ดพร้อมกรอบ สคริปต์นี้ตัดเมล็ดตามกรอบ เก็บเฉพาะ 7 คลาสของโจทย์ แยกโฟลเดอร์ตามคลาส

```bat
cd C:\tesa-pi
python scripts\crop_beans.py
```

ได้ `datasets\beans-cls\{train,val,test}\{7 คลาส}` และตารางจำนวนเมล็ดต่อคลาส

### 4.2 เทรน classifier 💻 `(.venv)`

```bat
yolo classify train model=yolo26n-cls.pt data=datasets/beans-cls epochs=60 imgsz=320 device=0 name=cls_v2
```

- `classify` = จำแนกทั้งภาพ (ภาพละ 1 เมล็ด → 1 คลาส)
- `yolo26n-cls.pt` = โมเดลตั้งต้นขนาดเล็กสุด ดาวน์โหลดอัตโนมัติ
- `epochs=60` จำนวนรอบ · `imgsz=320` ขนาดภาพ · `device=0` ใช้ GPU ตัวแรก
- ผลอยู่ที่ `runs\classify\cls_v2\` (โมเดล `weights\best.pt` · ดู `confusion_matrix_normalized.png`)

ใช้เวลาไม่กี่นาทีบน RTX 4060 · ผลที่เราได้: top1 ≈ 0.865 (val)

### 4.3 วัดผลกับชุด test 💻 `(.venv)`

```bat
yolo classify val model=runs\classify\cls_v2\weights\best.pt data=datasets/beans-cls split=test imgsz=320
```

### 4.4 แปลงเป็น NCNN 💻 `(.venv)`

```bat
yolo export model=runs\classify\cls_v2\weights\best.pt format=ncnn imgsz=320
```

(ใช้โมเดลใน repo: แทน path ด้วย `models\cls_v2.pt`)

ได้โฟลเดอร์ `best_ncnn_model` ข้างไฟล์ `.pt` · `imgsz` ต้องตรงกับตอนเทรน

---

## 5. เตรียม Raspberry Pi

### 5.1 ลง OS 💻

1. ดาวน์โหลด **Raspberry Pi Imager** (Windows) → เสียบ microSD
2. Device: **Raspberry Pi 5** · OS: **Raspberry Pi OS (64-bit)** · Storage: การ์ด
3. Edit Settings:
   - hostname `tesa-pi` · username `admin` · ตั้งรหัสผ่าน
   - Wi-Fi: ชื่อ/รหัส (hotspot มือถือยืดหยุ่นสุด) · Wireless LAN country **TH**
   - Locale: Asia/Bangkok · keyboard **us**
   - Services: **Enable SSH** (password)
4. เขียนการ์ด → เสียบเข้า Pi → เสียบไฟ รอ 1–2 นาที

### 5.2 SSH เข้า Pi 💻

**SSH** = สั่งงาน Pi จากคอมผ่านเครือข่าย ไม่ต้องต่อจอ · คอมกับ Pi ต้องอยู่ Wi-Fi วงเดียวกัน

```bat
ssh admin@tesa-pi.local
```

ครั้งแรกตอบ `yes` แล้วใส่รหัส (ตอนพิมพ์รหัสไม่มีตัวอักษรขึ้น เป็นเรื่องปกติ)

> เจอ `REMOTE HOST IDENTIFICATION HAS CHANGED` หลังลง OS ใหม่ → `ssh-keygen -R tesa-pi.local` แล้ว SSH ใหม่

### 5.3 ติดตั้งของบน Pi 🍓

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y tmux time mosquitto mosquitto-clients
mkdir ~/tesa && cd ~/tesa
python3 -m venv .venv
source .venv/bin/activate
pip install ultralytics ncnn pyyaml gradio paho-mqtt
```

- `tmux` = หน้าต่างที่รันต่อได้แม้ SSH หลุด · `mosquitto` = MQTT broker จำลองไว้ทดสอบ
- ติดตั้งนาน ควรรันใน tmux และใช้ Wi-Fi บ้าน (ไฟล์ใหญ่หลายร้อย MB)

### 5.4 ทุกครั้งที่ SSH เข้า Pi 🍓

```bash
tmux attach -t tesa      # ถ้าขึ้น "no sessions" ใช้: tmux new -s tesa
cd ~/tesa
source .venv/bin/activate
```

ออกจาก tmux โดยงานยังรัน: `Ctrl + B` แล้วกด `D`

---

## 6. ส่งโมเดลและโค้ดไป Pi

รันบน 💻 **คอม** (หน้าต่างธรรมดา ไม่ใช่หน้าต่าง SSH)

```bat
cd C:\tesa-pi
scp -r runs\classify\cls_v2\weights\best_ncnn_model admin@tesa-pi.local:~/tesa/cls_v2_ncnn_model
scp -r grader admin@tesa-pi.local:~/tesa/
scp scripts\eval_cls_pi.py admin@tesa-pi.local:~/tesa/
scp -r datasets\beans-cls\test admin@tesa-pi.local:~/tesa/beans-test
scp -r datasets\robusta-digkit3\test\images admin@tesa-pi.local:~/tesa/full-test
```

> ⚠️ ชื่อโฟลเดอร์โมเดลบน Pi **ต้องลงท้ายด้วย `_ncnn_model`** ไม่งั้น Ultralytics ไม่รู้จัก (error: `is not a supported model format`)

เช็กบน 🍓: `ls ~/tesa` ต้องเห็น `cls_v2_ncnn_model`, `grader`, `beans-test`, `full-test`

---

## 7. ทดสอบบน Pi 🍓 `(.venv)`

### 7.1 สูตรเกรด

```bash
python grader/grade.py
```

ต้องขึ้น `[PASS]` 5 บรรทัด + `ทุกกรณีผ่าน ✅`

### 7.2 ความแม่นและความเร็วของโมเดล

```bash
python eval_cls_pi.py
```

ได้ความแม่นต่อคลาส + เวลาต่อเม็ด (เราได้ ~11.7 ms/เม็ด)

### 7.3 Pipeline ทั้งสาย (command line)

```bash
python grader/pipeline.py full-test/*.jpg --lot TEST-ALL
```

ได้ `results/TEST-ALL.json` และภาพวาดกรอบ `results/*_annotated.jpg`

ดึงผลมาดูบนคอม 💻: `scp -r admin@tesa-pi.local:~/tesa/results pi-results`

---

## 8. เปิดหน้าเว็บ Bean Grader

1. 🍓 รันโปรแกรม (ใน tmux)

```bash
python grader/app.py
```

รอจนขึ้น `Running on local URL: http://0.0.0.0:7860`

2. 🍓 ดู IP ของ Pi (หน้าต่าง SSH อีกอัน): `hostname -I`
3. 💻 เปิดเบราว์เซอร์: `http://<IP ของ Pi>:7860` เช่น `http://192.168.1.175:7860`
4. อัปโหลดภาพ (หลายภาพ = ล็อตเดียว) → ใส่รหัสล็อต → **ตรวจเกรด**
5. หยุดโปรแกรม: `Ctrl + C`

**เปิดไม่ได้?** ใช้อุโมงค์ SSH (ไม่ต้องสนใจ IP):

```bat
ssh -L 7860:localhost:7860 admin@tesa-pi.local
```

เปิดหน้าต่างนี้ค้างไว้ แล้วเปิด `http://localhost:7860`

---

## 9. ส่งผลผ่าน MQTT

**MQTT** = ระบบส่งข้อความผ่านตัวกลาง (broker) · Pi ส่ง (publish) · server รับ (subscribe)

### 9.1 ทดสอบในเครื่อง 🍓

หน้าต่าง A รอรับ:

```bash
mosquitto_sub -h localhost -t "coffee/+/ai_results" -v
```

หน้าต่าง B: เปิด `grader/app.py` แล้วกดตรวจเกรดบนเว็บ (ติ๊ก "ส่งผลไป server อัตโนมัติ")

หน้าต่าง A ต้องขึ้น เช่น

```
coffee/LOT01/ai_results {"good": 9, "shell": 0, "full_black": 5, "broken": 0, "parchment": 2, "hull_husk": 15, "immature": 21, "defect_ratio": 82.69}
```

### 9.2 ใช้กับ server จริง

แก้ `grader/mqtt.yaml` บรรทัด `host:` เป็นที่อยู่ broker จริง แล้วรัน app ใหม่ · ส่งซ้ำได้ด้วยปุ่ม "ส่งผลล่าสุดไป server อีกครั้ง"

---

## 10. ปรับแต่ง

| อยากเปลี่ยน | แก้ที่ |
|---|---|
| เส้นแบ่งเกรด A/B/C, น้ำหนักแต่ละคลาส | `grader/grading.yaml` |
| broker / topic / ชื่อฟิลด์ที่ส่ง server | `grader/mqtt.yaml` |
| โมเดลที่ใช้, ขนาดภาพ, ความไวการตัดเมล็ด | ส่วนตั้งค่าบนสุดของ `grader/pipeline.py` (`MODEL`, `IMGSZ`, `MIN_AREA_FRAC`) |
| คลาสของ dataset ใหม่ | `CLASS_MAP` ใน `scripts/crop_beans.py` แล้วเทรนใหม่ |

รายละเอียดเกณฑ์เกรด: [grading.md](grading.md)

---

## 11. แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| `'yolo' is not recognized` | ยังไม่ได้เข้า venv → `.venv\Scripts\activate` (คอม) / `source .venv/bin/activate` (Pi) |
| `No module named 'ultralytics'` / `'yaml'` | ไม่ได้อยู่ใน venv หรือยังไม่ได้ติดตั้ง → `pip install ultralytics` / `pip install pyyaml` |
| `ls is not recognized` | พิมพ์บนคอม ไม่ใช่ Pi → SSH เข้า Pi ก่อน |
| `torch.cuda.is_available()` = False | ติดตั้ง PyTorch ผิดตัว → ใช้คำสั่งจาก pytorch.org |
| `is not a supported model format` | ชื่อโฟลเดอร์ NCNN ต้องลงท้าย `_ncnn_model` |
| `scp: No such file or directory` | path ผิด หรือไฟล์ยังอยู่ใน Downloads |
| export NCNN โหลด `pnnx` ช้ามาก | `Ctrl + C` แล้ว `pip install pnnx` เอง จากนั้นรัน export ซ้ำ |
| เว็บ "ปฏิเสธการเชื่อมต่อ" | `tesa-pi.local` ชี้ IPv6 → ใช้ IP จาก `hostname -I` |
| เว็บ "ตอบกลับนานเกินไป" | คอมกับ Pi คนละวง → ต่อ Wi-Fi เดียวกัน หรือใช้อุโมงค์ SSH |
| SSH หลุดระหว่างติดตั้ง | ใช้ tmux · ถ้า apt ค้าง: `sudo dpkg --configure -a` |
| `tmux attach` ขึ้น `no sessions` | Pi รีบูตไปแล้ว → `tmux new -s tesa` |
| เกรดออก C เกือบทุกครั้ง | ปกติถ้าภาพมีเมล็ดเสียมาก (เกณฑ์ SCA เข้ม) ดูคำอธิบายใน [grading.md](grading.md) และ [results.md](results.md) |
| ภาพจาก dataset อื่นทายผิดเยอะ | domain shift: โมเดลเรียนจากภาพแบบเดียว → เทรนเพิ่มด้วยภาพแบบนั้น |

---

## 12. คำศัพท์

| คำ | ความหมาย |
|---|---|
| venv | กล่องแยกไลบรารี Python ของโปรเจกต์ |
| classifier | โมเดลที่บอกว่าภาพ (เมล็ด) เป็นคลาสอะไร |
| epoch | 1 รอบที่โมเดลเห็นข้อมูลเทรนครบทุกภาพ |
| top1 accuracy | สัดส่วนที่ทายคลาสถูก |
| confusion matrix | ตารางว่าคลาสจริงแต่ละคลาส ถูกทายเป็นอะไรบ้าง |
| NCNN | รูปแบบโมเดลที่รันบน CPU แบบ ARM (Pi) ได้เร็ว ไม่ต้องใช้ PyTorch |
| inference / predict | ใช้โมเดลทำนายภาพใหม่ (ไม่ได้เทรน) |
| full defect | หน่วยนับเมล็ดเสียตามมาตรฐาน SCA (เมล็ดดำ 1 เม็ด = 1, เมล็ดเสียอื่น 5 เม็ด = 1) |
| MQTT / broker / topic | ระบบส่งข้อความ / ตัวกลาง / ชื่อช่องทางของข้อความ |
| SSH / scp | สั่งงานเครื่องอื่นผ่านเครือข่าย / คัดลอกไฟล์ผ่าน SSH |
| tmux | หน้าต่าง terminal ที่รันต่อได้แม้ SSH หลุด |
