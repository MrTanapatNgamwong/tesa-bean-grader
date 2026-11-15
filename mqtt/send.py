"""
send.py — ส่งผลตรวจไป server ผ่าน MQTT ตามสเปกทีม server
  topic   : coffee/<LOT_ID>/ai_results
  payload : {"good":92,"shell":2,"full_black":1,"broken":3,"parchment":0,"hull_husk":0,"immature":0}
            จำนวนเมล็ดต่อคลาสจาก detect.py · การคิดเกรด/สัดส่วนทำที่ server
ตั้งค่าที่ mqtt.yaml · ทดสอบเดี่ยว: python mqtt/send.py results/ไฟล์.json
"""
import json
import re
import socket
import sys
from pathlib import Path

import paho.mqtt.publish as publish
import yaml

CONFIG_PATH = Path(__file__).with_name("mqtt.yaml")


def load_mqtt_config(path=CONFIG_PATH):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def safe_lot_id(lot_id):
    """MQTT topic ห้ามมี / + # และช่องว่าง → แทนด้วย _"""
    return re.sub(r"[/+#\s]", "_", str(lot_id)) or "LOT"


def build_payload(result, cfg):
    """แปลงผลตรวจของ detect.py → payload ตามสเปก server (จำนวนเมล็ด 7 คลาส)"""
    counts = result["counts"]
    return {server_name: int(counts.get(ours, 0)) for ours, server_name in cfg["field_map"].items()}


def send_result(result, cfg=None):
    """ส่งผลตรวจหนึ่งล็อต · คืน (สำเร็จไหม, ข้อความสถานะ)"""
    cfg = cfg or load_mqtt_config()
    if not cfg.get("enabled", True):
        return False, "ปิดการส่ง MQTT ไว้ (enabled: false)"
    topic = cfg["topic"].format(lot_id=safe_lot_id(result["lot_id"]))
    payload = json.dumps(build_payload(result, cfg))
    auth = {"username": cfg["username"], "password": cfg.get("password")} if cfg.get("username") else None
    tls = None
    if cfg.get("tls"):
        ca = cfg.get("ca_cert")
        if ca:  # ไฟล์ CA ที่ดาวน์โหลดจาก EMQX Cloud (path เทียบกับโฟลเดอร์ mqtt)
            ca_path = Path(ca) if Path(ca).is_absolute() else Path(__file__).parent / ca
            if not ca_path.exists():
                return False, f"ไม่พบไฟล์ CA: {ca_path}"
            tls = {"ca_certs": str(ca_path)}
        else:
            tls = {}  # ใช้ใบรับรองมาตรฐานของระบบ
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(cfg.get("timeout_s", 5))
    try:
        publish.single(topic, payload, qos=cfg.get("qos", 1), retain=cfg.get("retain", False), hostname=cfg["host"],
                       port=cfg.get("port", 1883), client_id=cfg.get("client_id", ""),
                       auth=auth, tls=tls)
        return True, f"ส่งแล้ว → {cfg['host']}:{cfg.get('port', 1883)} · {topic} · {payload}"
    except Exception as e:  # broker ไม่เปิด, ต่อไม่ถึง ฯลฯ
        return False, f"ส่งไม่สำเร็จ ({cfg['host']}:{cfg.get('port', 1883)}): {type(e).__name__}: {e}"
    finally:
        socket.setdefaulttimeout(old_timeout)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("ใช้: python mqtt/send.py results/ไฟล์.json")
    ok, msg = send_result(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    print(("✅ " if ok else "❌ ") + msg)
