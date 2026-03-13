import copy
import io
import importlib
import json
import os
import re
import textwrap
from datetime import datetime

from groq import Groq


def parse_manual_weakness_topics(text: str) -> list[str]:
    raw = str(text or "").strip()
    if not raw:
        return []
    topics = [p.strip() for p in re.split(r"[,\n;/|]+", raw) if p.strip()]
    unique_topics = []
    seen = set()
    for topic in topics:
        key = topic.lower()
        if key not in seen:
            seen.add(key)
            unique_topics.append(topic)
    return unique_topics[:10]


def build_effective_weakness_counts(auto_counts: dict, manual_text: str) -> dict:
    merged = copy.deepcopy(auto_counts) if isinstance(auto_counts, dict) else {}
    for topic in parse_manual_weakness_topics(manual_text):
        merged[topic] = merged.get(topic, 0) + 3
    return merged


def parse_json_from_model_text(text: str) -> dict | None:
    raw = str(text or "").strip()
    if not raw:
        return None

    fenced_json = re.search(r"```json\s*(.*?)```", raw, flags=re.IGNORECASE | re.DOTALL)
    if fenced_json:
        raw = fenced_json.group(1).strip()
    else:
        fenced_any = re.search(r"```\s*(.*?)```", raw, flags=re.DOTALL)
        if fenced_any:
            raw = fenced_any.group(1).strip()

    try:
        return json.loads(raw)
    except Exception:
        pass

    first_curly = raw.find("{")
    last_curly = raw.rfind("}")
    if first_curly >= 0 and last_curly > first_curly:
        try:
            return json.loads(raw[first_curly:last_curly + 1])
        except Exception:
            return None
    return None


def build_weakness_worksheet_payload(
    api_key: str,
    model_name: str,
    weakness_counts: dict,
    learner_level: str,
    language_pref: str,
    question_count: int,
) -> tuple[dict | None, str | None]:
    if not weakness_counts:
        return None, "ยังไม่มีข้อมูลหัวข้อที่ควรทบทวนในเซสชันนี้"

    top_weakness = sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    weakness_text = ", ".join([f"{topic} ({count})" for topic, count in top_weakness])

    system_prompt = (
        "คุณคือผู้ช่วยสร้างแบบฝึกหัดคณิตศาสตร์ส่วนบุคคลจากจุดอ่อนผู้เรียน\n"
        "ให้ตอบกลับเป็น JSON เท่านั้น"
    )
    user_prompt = (
        f"ข้อมูลผู้เรียน: ระดับ {learner_level} | ภาษา {language_pref}\n"
        f"หัวข้อที่พลาดบ่อย (เรียงจากมากไปน้อย): {weakness_text}\n"
        f"สร้างโจทย์จำนวน {question_count} ข้อ โดยเน้นหัวข้อที่พลาดมากที่สุด\n\n"
        "เงื่อนไข:\n"
        "1) โจทย์ต้องหลากหลายและเรียงจากง่ายไปยาก\n"
        "2) คำอธิบายเฉลยต้องเป็นขั้นตอนที่ทำตามได้\n"
        "3) สรุปคำตอบสุดท้ายของแต่ละข้อให้ชัดเจน\n\n"
        "คืนค่าเป็น JSON รูปแบบนี้เท่านั้น:\n"
        "{\n"
        "  \"worksheet_title\": \"...\",\n"
        "  \"instructions\": \"...\",\n"
        "  \"questions\": [\n"
        "    {\n"
        "      \"number\": 1,\n"
        "      \"topic\": \"...\",\n"
        "      \"problem\": \"...\",\n"
        "      \"solution_steps\": [\"ขั้นที่ 1 ...\", \"ขั้นที่ 2 ...\"],\n"
        "      \"final_answer\": \"...\"\n"
        "    }\n"
        "  ]\n"
        "}"
    )

    try:
        client = Groq(api_key=api_key.strip())
        resp = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception as e:
        return None, f"เรียก AI ไม่สำเร็จ: {e}"

    raw = (resp.choices[0].message.content or "").strip()
    payload = parse_json_from_model_text(raw)
    if not isinstance(payload, dict):
        return None, "AI ส่งผลลัพธ์ไม่ใช่ JSON ที่ถูกต้อง"

    questions = payload.get("questions", [])
    if not isinstance(questions, list) or not questions:
        return None, "AI ไม่ได้ส่งรายการโจทย์กลับมา"

    normalized_questions = []
    for idx, item in enumerate(questions, 1):
        if not isinstance(item, dict):
            continue
        steps = item.get("solution_steps", [])
        if not isinstance(steps, list):
            steps = [str(steps)] if steps else []
        normalized_questions.append(
            {
                "number": idx,
                "topic": str(item.get("topic", "หัวข้อผสม")).strip() or "หัวข้อผสม",
                "problem": str(item.get("problem", "")).strip() or "(ไม่มีข้อความโจทย์)",
                "solution_steps": [str(s).strip() for s in steps if str(s).strip()],
                "final_answer": str(item.get("final_answer", "-")).strip() or "-",
            }
        )

    if not normalized_questions:
        return None, "AI ส่งรูปแบบโจทย์ไม่ครบ"

    return {
        "worksheet_title": str(payload.get("worksheet_title", "Smart Worksheet Generator")).strip() or "Smart Worksheet Generator",
        "instructions": str(payload.get("instructions", "ทำโจทย์ให้ครบทุกข้อ และตรวจคำตอบจากหน้าถัดไป")).strip(),
        "questions": normalized_questions[:question_count],
    }, None


def resolve_pdf_font_name(pdfmetrics_module, ttfonts_module) -> tuple[str, int]:
    register_font = getattr(pdfmetrics_module, "registerFont")
    get_registered_font_names = getattr(pdfmetrics_module, "getRegisteredFontNames")
    TTFont = getattr(ttfonts_module, "TTFont")

    preferred_font_name = "TutorThai"
    registered = set(get_registered_font_names())
    if preferred_font_name in registered:
        return preferred_font_name, 95

    font_candidates = [
        r"C:\Windows\Fonts\tahoma.ttf",
        r"C:\Windows\Fonts\LeelawUI.ttf",
        r"C:\Windows\Fonts\THSarabunNew.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansThaiUI-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/System/Library/Fonts/Supplemental/Thonburi.ttf",
        "assets/fonts/NotoSansThai-Regular.ttf",
        "NotoSansThai-Regular.ttf",
    ]

    for font_path in font_candidates:
        if not os.path.exists(font_path):
            continue
        try:
            register_font(TTFont(preferred_font_name, font_path))
            return preferred_font_name, 95
        except Exception:
            registered_after = set(get_registered_font_names())
            if preferred_font_name in registered_after:
                return preferred_font_name, 95
            continue

    return "Helvetica", 105


def build_weakness_worksheet_pdf_bytes(worksheet: dict, weakness_counts: dict) -> tuple[bytes | None, str | None]:
    try:
        pagesizes_module = importlib.import_module("reportlab.lib.pagesizes")
        pdfgen_canvas_module = importlib.import_module("reportlab.pdfgen.canvas")
        pdfmetrics_module = importlib.import_module("reportlab.pdfbase.pdfmetrics")
        ttfonts_module = importlib.import_module("reportlab.pdfbase.ttfonts")
    except Exception:
        return None, "ยังไม่พบแพ็กเกจ reportlab (ติดตั้งด้วย pip install reportlab)"

    A4 = getattr(pagesizes_module, "A4")
    Canvas = getattr(pdfgen_canvas_module, "Canvas")

    buffer = io.BytesIO()
    pdf = Canvas(buffer, pagesize=A4)
    _, page_height = A4

    font_name, wrap_width = resolve_pdf_font_name(pdfmetrics_module, ttfonts_module)

    margin_x = 40
    y = page_height - 46
    body_font_size = 11
    line_height = 15

    def new_page():
        nonlocal y
        pdf.showPage()
        pdf.setFont(font_name, body_font_size)
        y = page_height - 46

    def write_line(text: str, indent: int = 0):
        nonlocal y
        if y < 55:
            new_page()
        pdf.drawString(margin_x + indent, y, text)
        y -= line_height

    def write_paragraph(text: str, indent: int = 0, gap_after: int = 4):
        nonlocal y
        para = str(text or "").strip()
        if not para:
            y -= gap_after
            return
        for raw_line in para.splitlines() or [""]:
            chunks = textwrap.wrap(raw_line, width=max(20, wrap_width - (indent // 2)), replace_whitespace=False) or [""]
            for chunk in chunks:
                write_line(chunk, indent=indent)
        y -= gap_after

    questions = worksheet.get("questions", []) if isinstance(worksheet, dict) else []
    if not questions:
        return None, "ไม่มีข้อมูลโจทย์สำหรับสร้าง PDF"

    pdf.setTitle("Smart Weakness Worksheet")
    pdf.setFont(font_name, 16)
    write_line(str(worksheet.get("worksheet_title", "Smart Worksheet Generator")))
    pdf.setFont(font_name, body_font_size)
    write_line(f"สร้างเมื่อ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y -= 6

    tops = sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    if tops:
        write_line("จุดอ่อนที่ใช้สร้างใบงาน:")
        for topic, count in tops:
            write_line(f"- {topic} ({count} ครั้ง)", indent=12)
        y -= 4

    write_paragraph(f"คำแนะนำ: {worksheet.get('instructions', 'ทำโจทย์ให้ครบทุกข้อ และตรวจคำตอบจากหน้าถัดไป')}")
    write_line("โจทย์ (หน้าแบบฝึกหัด)")
    y -= 2

    for idx, q in enumerate(questions, 1):
        topic = str(q.get("topic", "หัวข้อผสม"))
        problem = str(q.get("problem", "(ไม่มีข้อความโจทย์)"))
        write_line(f"ข้อ {idx} [{topic}]", indent=2)
        write_paragraph(problem, indent=16, gap_after=6)

    new_page()
    pdf.setFont(font_name, 15)
    write_line("เฉลยละเอียด (หน้านี้สำหรับตรวจคำตอบ)")
    pdf.setFont(font_name, body_font_size)
    y -= 4

    for idx, q in enumerate(questions, 1):
        topic = str(q.get("topic", "หัวข้อผสม"))
        steps = q.get("solution_steps", [])
        if not isinstance(steps, list):
            steps = [str(steps)] if steps else []
        final_answer = str(q.get("final_answer", "-"))

        write_line(f"ข้อ {idx} [{topic}]", indent=2)
        if not steps:
            write_paragraph("1) (ไม่มีขั้นตอนที่ส่งกลับมา)", indent=16, gap_after=2)
        else:
            for step_i, step in enumerate(steps, 1):
                write_paragraph(f"{step_i}) {str(step)}", indent=16, gap_after=2)
        write_paragraph(f"คำตอบสุดท้าย: {final_answer}", indent=16, gap_after=7)

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue(), None
