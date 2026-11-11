"""
app.py — หน้าต่างโปรแกรม Bean Grader (Gradio 6)
อัปโหลดภาพเมล็ดกาแฟ → กดตรวจ → เกรด A/B/C + สัดส่วนดี/เสีย + จำนวนต่อคลาส + ภาพวาดกรอบ + JSON

วิธีรัน (บน Pi ที่ ~/tesa ใน venv):
    python grader/app.py
เปิดจากคอม:  http://<IP ของ Pi>:7860  หรือผ่านอุโมงค์ SSH แล้วเปิด http://localhost:7860
"""
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import gradio as gr

sys.path.insert(0, str(Path(__file__).parent))
from grade import grade, load_config, merge_counts  # noqa: E402
from pipeline import COLORS, DEVICE_ID, MODEL, OUT_DIR, process_image  # noqa: E402
from send import load_mqtt_config, send_result  # noqa: E402

# ===== ข้อความและสี =====
GRADE_STYLE = {  # เกรด → (สี, ความหมาย)
    "A": ("#2e7d32", "Specialty / Premium"),
    "B": ("#e0a100", "Exchange · เกรดซื้อขายทั่วไป"),
    "C": ("#c62828", "Below standard / Off grade"),
}
CLASS_TH = {
    "good": "เมล็ดดี", "full_black": "เมล็ดดำ", "husk": "เปลือก/ผลแห้ง", "shell": "หูช้าง",
    "broken": "แตกหัก", "parchment": "ติดกะลา", "immature": "ดิบ/อ่อน",
}


def bgr_hex(bgr):
    b, g, r = bgr
    return f"#{r:02x}{g:02x}{b:02x}"


# โหลดโมเดลและเกณฑ์ครั้งเดียวตอนเปิดโปรแกรม
from ultralytics import YOLO  # noqa: E402
model = YOLO(MODEL, task="classify")
cfg = load_config()
OUT_DIR.mkdir(exist_ok=True)


# ===== ส่วนสร้าง HTML ผลลัพธ์ =====
def empty_panel():
    return ("<div class='bg-empty'>☕<br>อัปโหลดภาพเมล็ดกาแฟ แล้วกด <b>ตรวจเกรด</b>"
            "<br><span>รองรับหลายภาพ · ทุกภาพในครั้งเดียวนับเป็นล็อตเดียวกัน</span></div>")


def result_panel(r):
    color, meaning = GRADE_STYLE.get(r["grade"], ("#555", ""))
    total = r["total_beans"]
    metrics = [
        ("เมล็ดทั้งหมด", f"{total}", "เม็ด"),
        ("เมล็ดดี", f"{r['good_ratio']:.1%}", f"{r['good_beans']} เม็ด"),
        ("เมล็ดเสีย", f"{r['defect_ratio']:.1%}", f"{r['defect_beans']} เม็ด"),
        ("Full defects / 350 g", f"{r['full_defects_per_350g']}",
         f"หมวด 1: {r['full_defects']['cat1']} · หมวด 2: {r['full_defects']['cat2']}"),
    ]
    cards = "".join(f"<div class='bg-card'><div class='bg-k'>{k}</div><div class='bg-v'>{v}</div>"
                    f"<div class='bg-s'>{s}</div></div>" for k, v, s in metrics)

    max_n = max(r["counts"].values()) or 1
    bars = ""
    for cls, n in sorted(r["counts"].items(), key=lambda x: -x[1]):
        pct = n / total
        bars += (f"<div class='bg-row'><div class='bg-name'><span class='bg-dot' style='background:{bgr_hex(COLORS.get(cls, (128,128,128)))}'></span>"
                 f"{cls}<small>{CLASS_TH.get(cls, '')}</small></div>"
                 f"<div class='bg-track'><div class='bg-fill' style='width:{n / max_n * 100:.1f}%;"
                 f"background:{bgr_hex(COLORS.get(cls, (128,128,128)))}'></div></div>"
                 f"<div class='bg-num'>{n}<small>{pct:.0%}</small></div></div>")

    warn = f"<div class='bg-warn'>⚠ {r['warning']}</div>" if r["warning"] else ""
    return f"""
    <div class='bg-top'>
      <div class='bg-badge' style='background:{color}'>{r['grade']}</div>
      <div>
        <div class='bg-title'>เกรด {r['grade']}</div>
        <div class='bg-mean'>{meaning}</div>
        <div class='bg-meta'>ล็อต {r['lot_id']} · {r['image_count']} ภาพ · {r['processing_ms'] / 1000:.1f} s · เกณฑ์ {r['grading_rule']}</div>
      </div>
    </div>
    {warn}
    <div class='bg-cards'>{cards}</div>
    <div class='bg-h'>จำนวนต่อคลาส</div>
    {bars}
    """


# ===== งานหลักเมื่อกดปุ่ม =====
def send_status(ok, msg):
    color = "#2e7d32" if ok else "#c62828"
    return f"<div style='color:{color};font-weight:600'>{'✅' if ok else '❌'} MQTT · {msg}</div>"


def run(files, lot_id, auto_send):
    if not files:
        raise gr.Error("ยังไม่ได้เลือกภาพ")
    lot_id = (lot_id or "").strip() or datetime.now().strftime("LOT-%Y%m%d-%H%M%S")

    t0 = time.perf_counter()
    all_counts, images_meta, annotated = [], [], []
    for f in files:
        counts, meta = process_image(model, Path(f), OUT_DIR)
        all_counts.append(counts)
        images_meta.append(meta)
        annotated.append((str(OUT_DIR / meta["annotated_image"]),
                          f"{meta['filename']} · {meta['beans_detected']} เม็ด"))
    try:
        g = grade(merge_counts(*all_counts), cfg)
    except ValueError as e:
        raise gr.Error(str(e))

    result = {
        "lot_id": lot_id,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "device_id": DEVICE_ID,
        "model": Path(MODEL).name,
        "image_count": len(images_meta),
        **g,
        "images": images_meta,
        "processing_ms": round((time.perf_counter() - t0) * 1000, 1),
    }
    out_json = OUT_DIR / f"{lot_id}.json"
    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    status = send_status(*send_result(result)) if auto_send else "<div style='opacity:.6'>ยังไม่ได้ส่ง server</div>"
    return result_panel(result), annotated, result, str(out_json), result, status


def send_last(result):
    if not result:
        raise gr.Error("ยังไม่มีผลตรวจให้ส่ง กดตรวจเกรดก่อน")
    return send_status(*send_result(result))


def clear():
    return None, "", empty_panel(), [], None, None, None, ""


# ===== หน้าตา =====
CSS = """
.gradio-container {max-width: 1200px !important; margin: auto;}
#bg-header {background: linear-gradient(120deg, #3e2a1f, #6b4a32); color: #fff; border-radius: 14px;
            padding: 18px 24px;}
#bg-header h1 {margin: 0; font-size: 26px; color: #fff;}
#bg-header p {margin: 4px 0 0; opacity: .85; color: #f3e6d8;}
.bg-empty {text-align: center; padding: 60px 10px; font-size: 18px; color: var(--body-text-color-subdued);}
.bg-empty span {font-size: 13px;}
.bg-top {display: flex; gap: 18px; align-items: center; margin-bottom: 14px;}
.bg-badge {width: 96px; height: 96px; border-radius: 50%; color: #fff; font-size: 56px; font-weight: 800;
           display: flex; align-items: center; justify-content: center; flex: none;}
.bg-title {font-size: 26px; font-weight: 700;}
.bg-mean {font-size: 15px; opacity: .85;}
.bg-meta {font-size: 12px; opacity: .65; margin-top: 4px;}
.bg-warn {background: #fff4e5; color: #8a4b00; border-radius: 8px; padding: 8px 12px; margin-bottom: 12px;}
.bg-cards {display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px;}
.bg-card {border: 1px solid var(--border-color-primary); border-radius: 10px; padding: 10px 12px;}
.bg-k {font-size: 12px; opacity: .7;}
.bg-v {font-size: 24px; font-weight: 700;}
.bg-s {font-size: 11px; opacity: .6;}
.bg-h {font-weight: 600; margin: 4px 0 8px;}
.bg-row {display: grid; grid-template-columns: 170px 1fr 70px; gap: 10px; align-items: center; margin: 6px 0;}
.bg-name small, .bg-num small {display: block; font-size: 11px; opacity: .6;}
.bg-dot {display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px;}
.bg-track {background: var(--background-fill-secondary); border-radius: 6px; height: 14px; overflow: hidden;}
.bg-fill {height: 100%; border-radius: 6px;}
.bg-num {text-align: right; font-weight: 600;}
#bg-rule {font-size: 13px;}
@media (max-width: 800px) {.bg-cards {grid-template-columns: repeat(2, 1fr);} .bg-row {grid-template-columns: 120px 1fr 60px;}}
"""

THEME = gr.themes.Soft(primary_hue="amber", neutral_hue="stone")

with gr.Blocks(title="Bean Grader") as demo:
    gr.HTML("<div id='bg-header'><h1>☕ Bean Grader</h1>"
            "<p>ตรวจเกรดเมล็ดกาแฟโรบัสต้าดิบ · Edge AI บน Raspberry Pi 5</p></div>")
    with gr.Row(equal_height=False):
        with gr.Column(scale=4):
            files = gr.File(label="ภาพเมล็ดกาแฟ", file_count="multiple", file_types=["image"],
                            type="filepath", height=200)
            lot = gr.Textbox(label="รหัสล็อต", placeholder="เว้นว่าง = ตั้งให้อัตโนมัติ")
            auto = gr.Checkbox(label="ส่งผลไป server อัตโนมัติหลังตรวจ (MQTT)", value=True)
            with gr.Row():
                btn = gr.Button("ตรวจเกรด", variant="primary", scale=3)
                clr = gr.Button("ล้าง", scale=1)
            snd = gr.Button("ส่งผลล่าสุดไป server อีกครั้ง", size="sm")
            mq = load_mqtt_config()
            gr.Markdown(f"<span style='font-size:12px;opacity:.7'>broker {mq['host']}:{mq['port']} · topic {mq['topic'].replace('{lot_id}', 'รหัสล็อต')}</span>")
            with gr.Accordion("เกณฑ์เกรด", open=False):
                gr.Markdown(
                    "Full defects ต่อตัวอย่าง 350 g (SCA/CQI)\n\n"
                    "| เกรด | full defects | ความหมาย |\n|---|---|---|\n"
                    "| **A** | ≤ 8 | Specialty / Premium |\n| **B** | 9 – 23 | Exchange |\n"
                    "| **C** | ≥ 24 | Below standard / Off grade |\n\n"
                    "Full black 1 เม็ด = 1 · คลาสเสียอื่น 5 เม็ด = 1", elem_id="bg-rule")
        with gr.Column(scale=7):
            status = gr.HTML()
            panel = gr.HTML(empty_panel())
    last = gr.State(None)  # เก็บผลตรวจล่าสุดไว้ส่งซ้ำ
    gallery = gr.Gallery(label="ผลตรวจรายภาพ", columns=3, height="auto", object_fit="contain")
    with gr.Accordion("ข้อมูลสำหรับ server (JSON)", open=False):
        with gr.Row():
            out_json = gr.JSON(scale=3)
            out_file = gr.File(label="ดาวน์โหลด JSON", scale=1)

    btn.click(run, inputs=[files, lot, auto], outputs=[panel, gallery, out_json, out_file, last, status])
    snd.click(send_last, inputs=[last], outputs=[status])
    clr.click(clear, outputs=[files, lot, panel, gallery, out_json, out_file, last, status])

if __name__ == "__main__":
    # 0.0.0.0 = เปิดให้เครื่องอื่นในวง Wi-Fi เข้าได้
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=THEME, css=CSS)
