"""
test_server_send.py — จำลองฝั่ง server: ส่งภาพไปให้ Pi แล้วรอผลกลับ (ใช้ทดสอบ / ให้ทีม server ดูเป็นตัวอย่าง)

    python mqtt/test_server_send.py ภาพ.jpg --lot LOT01

ส่ง  : coffee/LOT01/image        (ไฟล์ภาพทั้งไฟล์)
รอรับ: coffee/LOT01/ai_results   และ coffee/LOT01/ai_error
ใช้ broker จาก mqtt/mqtt.yaml
"""
import argparse
import sys
import time
from pathlib import Path

import paho.mqtt.client as mqtt

sys.path.insert(0, str(Path(__file__).resolve().parent))
from send import load_mqtt_config  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", type=Path)
    ap.add_argument("--lot", default="LOT01")
    ap.add_argument("--timeout", type=float, default=60)
    args = ap.parse_args()
    cfg = load_mqtt_config()
    img_topic = cfg.get("image_topic", "coffee/+/image").replace("+", args.lot)
    got = {}

    def on_connect(c, u, f, rc, p):
        c.subscribe([(f"coffee/{args.lot}/ai_results", 1), (f"coffee/{args.lot}/ai_error", 1)])
        data = args.image.read_bytes()
        c.publish(img_topic, data, qos=1)
        got["t0"] = time.perf_counter()
        print(f"📤 ส่ง {args.image.name} ({len(data) / 1024:.0f} KB) → {img_topic}")

    def on_message(c, u, msg):
        print(f"📥 {msg.topic} ({(time.perf_counter() - got['t0']) * 1000:.0f} ms)\n   {msg.payload.decode()}")
        got["done"] = True

    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=cfg.get("client_id", "tesa") + "-testserver")
    if cfg.get("username"):
        c.username_pw_set(cfg["username"], cfg.get("password"))
    if cfg.get("tls"):
        c.tls_set()
    c.on_connect, c.on_message = on_connect, on_message
    c.connect(cfg["host"], cfg.get("port", 1883))
    c.loop_start()
    end = time.time() + args.timeout
    while not got.get("done") and time.time() < end:
        time.sleep(0.1)
    c.loop_stop()
    if not got.get("done"):
        print(f"⌛ ไม่ได้รับผลใน {args.timeout:.0f} s · เช็กว่า listen.py บน Pi รันอยู่ และใช้ broker เดียวกัน")


if __name__ == "__main__":
    main()
