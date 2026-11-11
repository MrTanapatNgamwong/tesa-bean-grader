"""
grade.py — แปลงจำนวนเมล็ดต่อคลาส เป็นสัดส่วนดี/เสีย, full defects และเกรด A/B/C

ใช้ในโค้ดอื่น:
    from grade import load_config, grade
    cfg = load_config()
    result = grade({"good": 55, "broken": 3, "immature": 2}, cfg)

ทดสอบตัวเอง (รันได้ทั้งบนคอมและ Pi):
    python grade.py
"""
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).with_name("grading.yaml")


def load_config(path=CONFIG_PATH):
    """อ่านเกณฑ์จาก grading.yaml"""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def merge_counts(*counts_list):
    """รวมจำนวนจากหลายภาพของล็อตเดียวกัน เช่น merge_counts(img1, img2)"""
    total = {}
    for counts in counts_list:
        for cls, n in counts.items():
            total[cls] = total.get(cls, 0) + n
    return total


def grade(counts, cfg):
    """
    counts : dict ชื่อคลาส → จำนวนเม็ด เช่น {"good": 55, "broken": 3}
    คืนค่า dict ที่พร้อมใส่ลง JSON ส่ง server
    """
    known = {cfg["good_class"], *cfg["defects"]}
    unknown = set(counts) - known
    if unknown:
        raise ValueError(f"คลาสที่ไม่รู้จัก: {sorted(unknown)} · แก้ grading.yaml หรือชื่อคลาสของโมเดล")

    # ใส่ 0 ให้คลาสที่ไม่เจอ เพื่อให้ JSON มีครบทุกคลาสเสมอ
    full_counts = {cls: int(counts.get(cls, 0)) for cls in [cfg["good_class"], *cfg["defects"]]}
    total = sum(full_counts.values())
    if total == 0:
        raise ValueError("ไม่พบเมล็ดเลย (total = 0) คำนวณเกรดไม่ได้")

    good = full_counts[cfg["good_class"]]
    defect_beans = total - good

    # full defects แยกตามหมวด: จำนวนเม็ด ÷ กี่เม็ดต่อ 1 full defect
    fd = {1: 0.0, 2: 0.0}
    for cls, rule in cfg["defects"].items():
        fd[rule["category"]] += full_counts[cls] / rule["per_full_defect"]
    fd_total = fd[1] + fd[2]

    # ขยายสัดส่วนจากจำนวนเม็ดที่นับได้ ให้เทียบกับตัวอย่าง 350 g
    per_350g = fd_total / total * cfg["beans_per_350g"]

    letter = None
    for g in cfg["grades"]:
        if g["max"] is None or per_350g <= g["max"]:
            letter = g["grade"]
            break

    warning = None
    if total < cfg["min_beans_warning"]:
        warning = f"เมล็ดน้อย ({total} เม็ด) เกรดอาจคลาดเคลื่อน ควรรวมหลายภาพ"

    return {
        "counts": full_counts,
        "total_beans": total,
        "good_beans": good,
        "defect_beans": defect_beans,
        "good_ratio": round(good / total, 4),
        "defect_ratio": round(defect_beans / total, 4),
        "full_defects": {"cat1": round(fd[1], 2), "cat2": round(fd[2], 2), "total": round(fd_total, 2)},
        "full_defects_per_350g": round(per_350g, 1),
        "grade": letter,
        "grading_rule": cfg["rule_name"],
        "warning": warning,
    }


def _self_test():
    """ตรวจสูตรกับตัวอย่างที่คำนวณมือไว้ในหน้า Notion"""
    cfg = load_config()
    cases = [
        ("broken 1 in 60",               {"good": 59, "broken": 1},                  7.2,  "A"),
        ("broken 3 in 60",               {"good": 57, "broken": 3},                  21.6, "B"),
        ("broken 3 + immature 2 in 60",  {"good": 55, "broken": 3, "immature": 2},   36.0, "C"),
        ("full_black 1 in 60",           {"good": 59, "full_black": 1},              36.0, "C"),
        ("all good, 20 beans (warning)", {"good": 20},                                0.0,  "A"),
    ]
    ok = True
    for name, counts, exp_350, exp_grade in cases:
        r = grade(counts, cfg)
        passed = abs(r["full_defects_per_350g"] - exp_350) < 0.05 and r["grade"] == exp_grade
        ok &= passed
        print(f"[{'PASS' if passed else 'FAIL'}] {name:<30} per_350g={r['full_defects_per_350g']:>5}  "
              f"grade={r['grade']}  defect_ratio={r['defect_ratio']}"
              + (f"  ⚠ {r['warning']}" if r["warning"] else ""))
    print("\nทุกกรณีผ่าน ✅" if ok else "\nมีกรณีไม่ผ่าน ❌")


if __name__ == "__main__":
    _self_test()
