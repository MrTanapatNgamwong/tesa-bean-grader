"""
listen.py — รอรับภาพจาก server ผ่าน MQTT → ตรวจจับ + นับ (detect.py) → ส่งผลกลับ (send.py)

  รับ  : coffee/<LOT_ID>/image        payload รับได้ 2 แบบ
            1) JSON {"lot_id": "...", "image": "<base64>"}  (image เป็น data URL "data:image/jpeg;base64,..." ก็ได้)
            2) ไฟล์ภาพ JPEG/PNG ทั้งไฟล์ (bytes)
            lot_id ใช้ค่าใน JSON ก่อน ถ้าไม่มีใช้จาก topic
  ส่ง  : coffee/<LOT_ID>/ai_results   payload = {"good":..,"shell":..,"full_black":..,"broken":..,
                                                 "parchment":..,"hull_husk":..,"immature":..}
  error: coffee/<LOT_ID>/ai_error     payload = {"error": "..."}

ตั้งค่า broker ที่ mqtt/mqtt.yaml (ไฟล์เดียวกับ send.py) · ชื่อ topic ขาเข้าแก้ได้ที่ image_topic ใน mqtt.yaml

วิธีรัน (บน Pi ที่ ~/tesa ใน venv · ควรรันใน tmux):
    python mqtt/listen.py
    python mqtt/listen.py --model cls_v5_ncnn_model
หยุด: Ctrl + C
"""
import argparse
import base64
import json
import queue
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import paho.mqtt.client as mqtt

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "detector"))
import detect  # noqa: E402  (find_beans, process_image, MODEL, IMGSZ)
from send import load_mqtt_config, safe_lot_id, send_result  # noqa: E402

INBOX = Path("incoming")          # เก็บภาพที่ได้รับ
OUT_DIR = Path("results")         # JSON + ภาพวาดกรอบ (เหมือน detect.py)
jobs = queue.Queue()              # ภาพที่รอประมวลผล (ทำทีละภาพตามลำดับ)


def build_tls(cfg):
    if not cfg.get("tls"):
        return None
    ca = cfg.get("ca_cert")
    return str(ca if Path(ca).is_absolute() else HERE / ca) if ca else ""


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"❌ ต่อ broker ไม่สำเร็จ: {reason_code}")
        return
    topic = userdata["sub_topic"]
    client.subscribe(topic, qos=userdata["cfg"].get("qos", 1))
    print(f"✅ ต่อ broker แล้ว · รอภาพที่ {topic}")


def on_message(client, userdata, msg):
    # ทำแค่บันทึกไฟล์แล้วเข้าคิว ไม่ประมวลผลในนี้ (ไม่งั้นการเชื่อมต่อจะค้างระหว่างรันโมเดล)
    m = re.fullmatch(userdata["topic_regex"], msg.topic)
    topic_lot = m.group(1) if m else "LOT"
    try:
        lot_id, img_bytes = parse_payload(msg.payload, topic_lot)
    except Exception as e:  # JSON/base64 เสีย → แจ้ง server แล้วรอข้อความถัดไป
        lot_id = safe_lot_id(topic_lot)
        err = f"payload ไม่ถูกต้อง: {type(e).__name__}: {e}"
        print(f"❌ {lot_id}: {err}")
        client.publish(f"coffee/{lot_id}/ai_error", json.dumps({"error": err}), qos=userdata["cfg"].get("qos", 1),
                       retain=userdata["cfg"].get("retain", False))
        return
    INBOX.mkdir(exist_ok=True)
    path = INBOX / f"{lot_id}_{datetime.now():%Y%m%d-%H%M%S-%f}.jpg"
    path.write_bytes(img_bytes)
    print(f"📥 {msg.topic} · lot {lot_id} · {len(img_bytes) / 1024:.0f} KB → {path}")
    jobs.put((lot_id, path))


def parse_payload(payload, topic_lot):
    """คืน (lot_id, bytes ของภาพ) · รองรับ JSON+base64 (สเปกทีม server) และไฟล์ภาพตรง ๆ"""
    if payload[:1] in (b"{", b"["):
        data = json.loads(payload.decode("utf-8"))
        img_b64 = data.get("image", "")
        if "," in img_b64:  # data URL: "data:image/jpeg;base64,<ข้อมูล>"
            img_b64 = img_b64.split(",", 1)[1]
        if not img_b64:
            raise ValueError('ไม่มีฟิลด์ "image"')
        return safe_lot_id(data.get("lot_id") or topic_lot), base64.b64decode(img_b64)
    return safe_lot_id(topic_lot), payload


def worker(model, class_names, cfg, client):
    while True:
        lot_id, path = jobs.get()
        t0 = time.perf_counter()
        try:
            info = detect.process_image(model, class_names, path, OUT_DIR)
            result = {
                "lot_id": lot_id,
                "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
                "device_id": detect.DEVICE_ID,
                "model": userdata_model,
                "image_count": 1,
                "total_beans": info["beans_detected"],
                "counts": info["counts"],
                "images": [info],
                "processing_ms": round((time.perf_counter() - t0) * 1000, 1),
            }
            (OUT_DIR / f"{lot_id}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            ok, msg = send_result(result, cfg)
            print(f"{'✅' if ok else '❌'} {lot_id}: {info['beans_detected']} เม็ด {info['counts']} "
                  f"({result['processing_ms']} ms) · {msg}")
        except Exception as e:  # ภาพเสีย ฯลฯ → แจ้ง server แล้วรอภาพถัดไป
            err = f"{type(e).__name__}: {e}"
            print(f"❌ {lot_id}: {err}")
            client.publish(f"coffee/{lot_id}/ai_error", json.dumps({"error": err}), qos=cfg.get("qos", 1),
                           retain=cfg.get("retain", False))
        finally:
            jobs.task_done()


def main():
    global userdata_model
    ap = argparse.ArgumentParser(description="รอรับภาพจาก server แล้วส่งผลกลับ")
    ap.add_argument("--model", default=detect.MODEL)
    args = ap.parse_args()
    userdata_model = Path(args.model).name

    cfg = load_mqtt_config()
    sub_topic = cfg.get("image_topic", "coffee/+/image")
    topic_regex = re.escape(sub_topic).replace(r"\+", "([^/]+)")

    from ultralytics import YOLO
    print(f"โหลดโมเดล {args.model} ...")
    model = YOLO(args.model, task="classify")
    model.predict(detect.np.zeros((detect.IMGSZ, detect.IMGSZ, 3), detect.np.uint8), imgsz=detect.IMGSZ, verbose=False)
    class_names = list(model.names.values())
    OUT_DIR.mkdir(exist_ok=True)

    # client_id ต้องไม่ซ้ำกับ send.py (broker จะตัดการเชื่อมต่อตัวที่ใช้ชื่อซ้ำ)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=cfg.get("client_id", "tesa-pi") + "-listen",
                         userdata={"cfg": cfg, "sub_topic": sub_topic, "topic_regex": topic_regex})
    if cfg.get("username"):
        client.username_pw_set(cfg["username"], cfg.get("password"))
    tls = build_tls(cfg)
    if tls is not None:
        client.tls_set(ca_certs=tls or None)
    client.on_connect = on_connect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=1, max_delay=10)  # หลุดแล้วต่อใหม่เอง

    threading.Thread(target=worker, args=(model, class_names, cfg, client), daemon=True).start()
    print(f"เชื่อมต่อ {cfg['host']}:{cfg.get('port', 1883)} ...")
    client.connect(cfg["host"], cfg.get("port", 1883), keepalive=30)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("\nหยุดแล้ว")


userdata_model = ""

if __name__ == "__main__":
    main()
