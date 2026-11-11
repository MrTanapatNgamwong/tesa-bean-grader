# Setup

## เครื่องเทรน (Windows · RTX 4060)

```bat
:: Python 3.13 (ตรงกับ Pi)
py -3.13 -m venv .venv
.venv\Scripts\activate
:: PyTorch CUDA: คำสั่งจาก pytorch.org (Stable / Windows / Pip / CUDA สูงสุด)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu134
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
pip install ultralytics opencv-python matplotlib pyyaml pnnx
```

## Raspberry Pi 5

1. Raspberry Pi Imager → Raspberry Pi OS 64-bit · hostname `tesa-pi` · user `admin` · เปิด SSH · keyboard `us` · Asia/Bangkok · WLAN TH
2. ตั้งค่าเครื่อง

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y tmux time mosquitto mosquitto-clients
mkdir ~/tesa && cd ~/tesa
python3 -m venv .venv && source .venv/bin/activate
pip install ultralytics ncnn pyyaml gradio paho-mqtt
```

ทุกครั้งที่ SSH เข้ามา: `tmux attach -t tesa` (หรือ `tmux new -s tesa`) → `cd ~/tesa` → `source .venv/bin/activate`

## เทรน → export → ส่งไป Pi

```bat
python scripts\crop_beans.py
yolo classify train model=yolo26n-cls.pt data=datasets/beans-cls epochs=60 imgsz=320 device=0 name=cls_v2
yolo export model=runs\classify\cls_v2\weights\best.pt format=ncnn imgsz=320
scp -r runs\classify\cls_v2\weights\best_ncnn_model admin@tesa-pi.local:~/tesa/cls_v2_ncnn_model
scp -r grader admin@tesa-pi.local:~/tesa/
```

⚠️ โฟลเดอร์ NCNN ต้องลงท้าย `_ncnn_model` ไม่งั้น Ultralytics ไม่รู้จัก

## เปิดเว็บ Bean Grader

```bash
python grader/app.py      # บน Pi
hostname -I               # ดู IP แล้วเปิด http://<IP>:7860
```

เปิดไม่ได้ (คนละวง / IPv6): `ssh -L 7860:localhost:7860 admin@tesa-pi.local` แล้วเปิด `http://localhost:7860`

## MQTT

- ทดสอบที่บ้าน: `mqtt.yaml` → `host: localhost` · ฟังด้วย `mosquitto_sub -h localhost -t "coffee/+/ai_results" -v`
- ในค่าย: เปลี่ยน `host` ตามที่ทีม server กำหนด
