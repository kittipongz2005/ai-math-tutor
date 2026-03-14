import streamlit as st
import PyPDF2
import time
import io
import os
import re
import base64
import copy
import textwrap
import json
import importlib
import contextlib
from datetime import datetime
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from groq import Groq
from ui_assets import apply_ui_decorations
from html_export import build_chat_export_html
from worksheet_ui import render_worksheet_generator_ui
from worksheet_tools import (
    resolve_pdf_font_name,
)


def get_cropper_func():
    try:
        cropper_module = importlib.import_module("streamlit_cropper")
        return getattr(cropper_module, "st_cropper", None)
    except Exception:
        return None

SUPABASE_AVAILABLE = True

STORE_PATH = Path(".math_tutor_store.json")


def get_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, default)
        return str(value) if value is not None else default
    except Exception:
        return default


SUPABASE_URL = get_secret("SUPABASE_URL", "")
SUPABASE_KEY = get_secret("SUPABASE_KEY", "")
SUPABASE_TABLE = get_secret("SUPABASE_TABLE", "math_tutor_store")
SUPABASE_USER_ID = get_secret("SUPABASE_USER_ID", "default_user")


def supabase_ready() -> bool:
    return SUPABASE_AVAILABLE and bool(SUPABASE_URL) and bool(SUPABASE_KEY)


@st.cache_resource(show_spinner=False)
def get_supabase_client(url: str, key: str):
    try:
        supabase_module = importlib.import_module("supabase")
        create_client = getattr(supabase_module, "create_client", None)
        if create_client is None:
            return None
        return create_client(url, key)
    except Exception:
        return None

# ─────────────────────────────────────────────
#  Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Math AI Tutor",
    page_icon="∑",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  UI Decorations (CSS/JS/KaTeX)
# ─────────────────────────────────────────────
apply_ui_decorations()

# ─────────────────────────────────────────────
#  Session State
# ─────────────────────────────────────────────
for key, val in {
    "messages": [],
    "pending_prompt": "",
    "weakness_counts": {},
    "socratic_continue": False,
    "socratic_can_continue": False,
    "chat_history": [],
    "quick_mode": "ติวละเอียด",
    "last_quick_mode": "ติวละเอียด",
    "current_chat_id": "",
    "current_chat_dirty": False,
    "pending_quick_mode_restore": "",
    "pending_last_mode_restore": "",
    "storage_loaded": False,
    "edit_message_index": -1,
    "edit_message_text": "",
    "enable_python_calc": True,
    "worksheet_export_content": "",
    "worksheet_export_name": "",
    "worksheet_export_ready": False,
    "manual_weakness_text": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ─────────────────────────────────────────────
#  Helper Functions
# ─────────────────────────────────────────────

def fix_latex(text: str) -> str:
    t = str(text)
    t = t.replace(r'\[', '$$').replace(r'\]', '$$')
    t = t.replace(r'\(', '$').replace(r'\)', '$')
    foreign = {
        'Wykładnik':'เลขชี้กำลัง','wykładnik':'เลขชี้กำลัง',
        'tích phân':'อินทิเกรต','Тогда':'ดังนั้น','тогда':'ดังนั้น',
        'Подставляем обратно':'แทนค่ากลับ','Ответ':'คำตอบสุดท้าย:',
        'Получаем':'จะได้ว่า','Следовательно':'สรุปได้ว่า',
        'Имеем':'เราจะได้','Где':'โดยที่',
    }
    for f, th in foreign.items():
        t = t.replace(f, th)
    return t


def ensure_math_renderable(text: str) -> str:
    t = str(text).strip()
    if not t:
        return t

    t = t.replace("−", "-")

    if t.count("\\left") != t.count("\\right"):
        t = t.replace("\\left", "").replace("\\right", "")

    open_brace = t.count("{")
    close_brace = t.count("}")
    if open_brace > close_brace and (open_brace - close_brace) <= 6:
        t += "}" * (open_brace - close_brace)

    open_paren = t.count("(")
    close_paren = t.count(")")
    if open_paren > close_paren and (open_paren - close_paren) <= 4:
        t += ")" * (open_paren - close_paren)

    if re.search(r'(^|\n)\s*[=+\-]\s*\\', t) and "$$" not in t:
        t = f"$$\n\\begin{{aligned}}\n{t}\n\\end{{aligned}}\n$$"
    if t.lstrip().startswith("&") and "\\end{aligned}" in t and "\\begin{aligned}" not in t:
        t = "\\begin{aligned}\n" + t
    if "\\begin{aligned}" in t and "\\end{aligned}" not in t:
        t += "\n\\end{aligned}"
    has_aligned = "\\begin{aligned}" in t and "\\end{aligned}" in t
    if has_aligned and "$$" not in t:
        t = f"$$\n{t}\n$$"
    has_cmds = bool(re.search(r'\\(frac|int|sum|sqrt|cdot|times|left|right|text)', t))
    if t.lstrip().startswith("&") and "$" not in t:
        t = f"$$\n\\begin{{aligned}}\n{t}\n\\end{{aligned}}\n$$"
    elif has_cmds and "$" not in t and "\\n" in t:
        t = f"$$\n{t}\n$$"
    return t


def beautify_answer_text(text: str, decorate_final: bool = True) -> str:
    t = fix_latex(text)
    t = ensure_math_renderable(t)
    if not decorate_final:
        return t
    pat = re.compile(r'(\*\*คำตอบสุดท้าย:?\*\*|คำตอบสุดท้าย:)\s*(.+)', re.DOTALL)
    m = pat.search(t)
    if not m:
        return t
    body = t[:m.start()].strip()
    final_expr = m.group(2).strip()
    if final_expr:
        final_expr = final_expr.replace("\\\\", "\\")
        final_expr = re.sub(r'^\$\$\s*', '', final_expr)
        final_expr = re.sub(r'\s*\$\$$', '', final_expr)
        final_expr = final_expr.strip()

    if final_expr and "$" not in final_expr:
        final_expr = f"$$ {final_expr} $$"
    # NOTE: Keep LaTeX outside HTML block so Streamlit/Katex can render math correctly.
    pretty = (
        '<div class="final-answer"><strong>✅ คำตอบสุดท้าย</strong></div>\n\n'
        f'{final_expr}'
    )
    return (body + "\n\n" if body else "") + pretty


def encode_image(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.convert('RGB').save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()


def count_tokens_approx(text) -> int:
    return max(1, len(str(text)) // 4)


def extract_topics(text: str) -> list:
    kw = {
        "พีชคณิต":   ["สมการ","แยกตัวประกอบ","กำลัง","log","พหุนาม","algebra"],
        "แคลคูลัส":  ["อนุพันธ์","อินทิเกรต","ลิมิต","ปริพันธ์","derivative","integral","limit"],
        "ตรีโกณมิติ":["sin","cos","tan","ตรีโกณ","เรเดียน","มุม"],
        "เรขาคณิต":  ["พื้นที่","ปริมาตร","วงกลม","สามเหลี่ยม","geometry"],
        "สถิติ":     ["ความน่าจะเป็น","ค่าเฉลี่ย","ส่วนเบี่ยงเบน","variance","probability"],
        "เมทริกซ์":  ["เมทริกซ์","det","determinant","eigen","เวกเตอร์","vector"],
    }
    low = text.lower()
    return [t for t, keys in kw.items() if any(k.lower() in low for k in keys)]


def update_weakness(text: str):
    for topic in extract_topics(text):
        st.session_state.weakness_counts[topic] = \
            st.session_state.weakness_counts.get(topic, 0) + 1


def clean_snippet(text: str, max_len=200) -> str:
    one = re.sub(r'\s+', ' ', str(text)).strip()
    return (one[:max_len] + "…") if len(one) > max_len else one


def strip_internal_tags(text: str) -> str:
    t = str(text)
    t = re.sub(r'\[\[STEP_STATUS:(DONE|CONTINUE)\]\]', '', t, flags=re.IGNORECASE)
    return t.strip()


def clean_content_for_export(text: str) -> str:
    t = strip_internal_tags(text)
    t = re.sub(r'<think>.*?</think>', '', t, flags=re.IGNORECASE | re.DOTALL)
    t = re.sub(r'<think>.*$', '', t, flags=re.IGNORECASE | re.DOTALL)
    t = t.replace('<think>', '').replace('</think>', '')
    return t.strip()


def is_socratic_done(text: str, force_done: bool = False) -> bool:
    if force_done:
        return True
    raw = str(text)
    if re.search(r'\[\[STEP_STATUS:DONE\]\]', raw, flags=re.IGNORECASE):
        return True
    lowered = raw.lower()
    done_markers = ["คำตอบสุดท้าย", "final answer", "สรุปคำตอบสุดท้าย", "เฉลยครบ"]
    return any(marker in lowered for marker in done_markers)


def violates_socratic_overview(text: str) -> bool:
    raw = str(text)
    lowered = raw.lower()

    patterns = [
        r'คำตอบสุดท้าย',
        r'\\boxed',
        r'final answer',
        r'=\s*[^\n=]{1,120}\+\s*C\b',
        r'\[\[STEP_STATUS:DONE\]\]',
    ]
    if any(re.search(p, raw, flags=re.IGNORECASE) for p in patterns):
        return True

    # ถ้ามีสมการยาวหลายบรรทัด + มีสัญญาณสรุปคำตอบ ให้ถือว่าหลุดเฉลย
    has_many_eq_lines = len(re.findall(r'^\s*[=]', raw, flags=re.MULTILINE)) >= 2
    if has_many_eq_lines and ("ดังนั้น" in lowered or "จึงได้" in lowered or "สรุป" in lowered):
        return True

    return False


def build_socratic_overview_fallback() -> str:
    return (
        "แผนการทำข้อนี้ (ภาพรวมก่อน ยังไม่เฉลย):\n\n"
        "1. เลือกวิธีหลักที่เหมาะกับรูปโจทย์\n"
        "2. จัดรูปสมการให้พร้อมแทนสูตร\n"
        "3. ทำทีละขั้นจนได้รูปใกล้คำตอบ\n"
        "4. ตรวจความถูกต้องของรูปสุดท้าย\n\n"
        "พร้อมแล้วกดปุ่ม ➡️ ไปต่อ\n"
        "[[STEP_STATUS:CONTINUE]]"
    )


def build_profile_prompt(level, speed, lang, mode) -> str:
    return (
        f"ผู้เรียน: ระดับ {level} | ความเร็ว: {speed} | ภาษา: {lang} | โหมด: {mode}\n"
        "ปรับเนื้อหาให้เหมาะกับระดับผู้เรียน และปรับความยาวคำอธิบายตามความเร็วที่เลือก"
    )


def build_empathy_prompt(enabled: bool) -> str:
    if not enabled:
        return ""
    return (
        "\n\nกติกาด้านจิตวิทยาการสอน (Empathy & Persona):\n"
        "- ประเมินระดับความหงุดหงิดของผู้เรียนจากบริบทแชทล่าสุดทุกครั้ง\n"
        "- ถ้าผู้เรียนตอบผิดซ้ำ/หลงทางเกิน 2 รอบ ให้ปรับน้ำเสียงเป็นกำลังใจ อ่อนโยน และชี้จุดผิดแบบเฉพาะเจาะจง\n"
        "- หลีกเลี่ยงคำพูดทื่อ ๆ หรือทำให้ผู้เรียนรู้สึกถูกตำหนิ\n"
        "- ตัวอย่างโทนปกติ: 'ถูกต้องครับ ไปขั้นต่อไปกันเลย'\n"
        "- ตัวอย่างโทนเมื่อผู้เรียนตอบผิดซ้ำ: 'เกือบเป๊ะแล้วครับ! มาถูกทางแล้วตรงเครื่องหมายบวก แต่ลองเช็คตัวเลขหน้า $x$ อีกนิดนึงนะครับ สู้ๆ ✌️'"
    )


def build_chat_export_text(messages: list) -> str:
    lines = []
    for msg in messages:
        role = "ผู้ใช้" if msg.get("role") == "user" else "AI"
        content = clean_content_for_export(str(msg.get("content", ""))).strip()
        lines.append(f"[{role}]\n{content}\n")
    return "\n".join(lines).strip()


def build_chat_export_markdown(messages: list) -> str:
    parts = ["# Math AI Tutor Chat Export", ""]
    for idx, msg in enumerate(messages, 1):
        role = "🧑 ผู้ใช้" if msg.get("role") == "user" else "🤖 AI"
        content = clean_content_for_export(str(msg.get("content", ""))).strip()
        parts.append(f"## {idx}. {role}")
        parts.append("")
        parts.append(content)
        parts.append("")
    return "\n".join(parts).strip()


def build_chat_export_pdf_bytes(messages: list) -> tuple[bytes | None, str | None]:
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
    page_width, page_height = A4

    font_name, wrap_width = resolve_pdf_font_name(pdfmetrics_module, ttfonts_module)

    margin_x = 42
    y = page_height - 48
    line_height = 15

    def new_page():
        nonlocal y
        pdf.showPage()
        pdf.setFont(font_name, 11)
        y = page_height - 48

    pdf.setTitle("Math AI Tutor Chat Export")
    pdf.setFont(font_name, 14)
    pdf.drawString(margin_x, y, "Math AI Tutor Chat Export")
    y -= 22
    pdf.setFont(font_name, 11)
    pdf.drawString(margin_x, y, datetime.now().strftime("Exported: %Y-%m-%d %H:%M:%S"))
    y -= 24

    for idx, msg in enumerate(messages, 1):
        role = "ผู้ใช้" if msg.get("role") == "user" else "AI"
        content = clean_content_for_export(str(msg.get("content", ""))).strip() or "(ว่าง)"
        header = f"{idx}. {role}"

        if y < 80:
            new_page()

        pdf.setFont(font_name, 11)
        pdf.drawString(margin_x, y, header)
        y -= line_height

        for raw_line in content.splitlines() or [""]:
            chunks = textwrap.wrap(raw_line, width=wrap_width, replace_whitespace=False) or [""]
            for chunk in chunks:
                if y < 55:
                    new_page()
                pdf.drawString(margin_x + 10, y, chunk)
                y -= line_height

        y -= 6

    pdf.save()
    buffer.seek(0)
    return buffer.getvalue(), None


def run_python_code_capture(code: str) -> tuple[bool, str]:
    out = io.StringIO()
    local_ns = {}
    try:
        with contextlib.redirect_stdout(out):
            exec(code, {"np": np, "math": __import__("math")}, local_ns)
        printed = out.getvalue().strip()
        if printed:
            return True, printed
        if "result" in local_ns:
            return True, str(local_ns["result"])
        return True, "(รันโค้ดสำเร็จ แต่ไม่มี output; แนะนำให้ print(result))"
    except Exception as e:
        return False, str(e)


def extract_math_latex_from_image(
    api_key: str,
    image_b64: str,
    preferred_model: str = "",
    prompt_hint: str = "",
) -> tuple[str | None, str | None]:
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        return None, f"สร้าง Groq client ไม่สำเร็จ: {e}"

    model_candidates = []
    if preferred_model and "vision" in preferred_model.lower():
        model_candidates.append(preferred_model)
    model_candidates.extend([
        "llama-3.2-90b-vision-preview",
        "llama-3.2-11b-vision-preview",
    ])

    seen = set()
    unique_models = []
    for model_name in model_candidates:
        if model_name not in seen:
            unique_models.append(model_name)
            seen.add(model_name)

    ocr_prompt = (
        "คุณคือ OCR คณิตศาสตร์สำหรับสกัดโจทย์จากภาพเท่านั้น\n"
        "งานของคุณ: อ่านข้อความและสมการในรูป แล้วแปลงเป็นข้อความ/LaTeX โดยห้ามเฉลยโจทย์\n"
        "ข้อกำหนด:\n"
        "1) ห้ามคำนวณ ห้ามอธิบายวิธีทำ ห้ามเฉลย\n"
        "2) รักษาโครงสร้างโจทย์เดิมให้มากที่สุด\n"
        "3) สมการต้องอยู่ในรูป LaTeX\n"
        "4) ถ้าอ่านไม่ชัดให้ใส่ [unclear]\n"
        "รูปแบบผลลัพธ์:\n"
        "[OCR_TEXT]\n"
        "...\n\n"
        "[OCR_LATEX]\n"
        "..."
    )

    if prompt_hint.strip():
        ocr_prompt += f"\n\nบริบทจากผู้ใช้ (ช่วยแยกแยะตัวอักษร): {prompt_hint.strip()[:500]}"

    last_error = ""
    for model_name in unique_models:
        try:
            resp = client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": ocr_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                        ],
                    }
                ],
                temperature=0,
                max_tokens=1200,
            )
            content = (resp.choices[0].message.content or "").strip()
            if content:
                return content, None
        except Exception as e:
            last_error = str(e)
            continue

    if not last_error:
        last_error = "Vision OCR ไม่ส่งข้อความกลับ"
    return None, f"สกัดข้อความจากรูปไม่สำเร็จ: {last_error}"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def now_pretty() -> str:
    return datetime.now().strftime("%d/%m %H:%M")


def sanitize_messages_for_storage(messages: list) -> list:
    sanitized = []
    for msg in messages:
        sanitized.append({
            "role": msg.get("role", "assistant"),
            "content": str(msg.get("content", "")),
            "response_style": msg.get("response_style"),
            "tutor_mode": msg.get("tutor_mode"),
        })
    return sanitized


def save_store():
    payload = {
        "chat_history": st.session_state.chat_history,
        "current_chat": {
            "messages": sanitize_messages_for_storage(st.session_state.messages),
            "weakness_counts": st.session_state.weakness_counts,
            "quick_mode": st.session_state.quick_mode,
            "last_quick_mode": st.session_state.last_quick_mode,
            "chat_id": st.session_state.current_chat_id,
            "dirty": st.session_state.current_chat_dirty,
        },
        "updated_at": now_iso(),
        "version": 1,
    }

    if supabase_ready():
        try:
            client = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)
            if client is not None:
                client.table(SUPABASE_TABLE).upsert(
                    {
                        "user_id": SUPABASE_USER_ID,
                        "payload": payload,
                        "updated_at": now_iso(),
                    },
                    on_conflict="user_id",
                ).execute()
                return
        except Exception:
            pass

    try:
        STORE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_store_once():
    if st.session_state.storage_loaded:
        return
    st.session_state.storage_loaded = True

    payload = None
    if supabase_ready():
        try:
            client = get_supabase_client(SUPABASE_URL, SUPABASE_KEY)
            if client is not None:
                result = client.table(SUPABASE_TABLE).select("payload").eq("user_id", SUPABASE_USER_ID).limit(1).execute()
                if result and getattr(result, "data", None):
                    payload = result.data[0].get("payload")
        except Exception:
            payload = None

    if payload is None:
        if not STORE_PATH.exists():
            return
        try:
            payload = json.loads(STORE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return

    history = payload.get("chat_history", [])
    if isinstance(history, list):
        st.session_state.chat_history = history[:30]

    current = payload.get("current_chat", {})
    if isinstance(current, dict):
        messages = current.get("messages", [])
        weakness = current.get("weakness_counts", {})
        quick_mode = current.get("quick_mode", st.session_state.quick_mode)
        last_mode = current.get("last_quick_mode", quick_mode)
        chat_id = current.get("chat_id", "")
        dirty = bool(current.get("dirty", False))

        if isinstance(messages, list):
            st.session_state.messages = messages
        if isinstance(weakness, dict):
            st.session_state.weakness_counts = weakness
        if quick_mode in ["ติวละเอียด", "ฝึกทีละขั้น", "เฉลยไว"]:
            st.session_state.quick_mode = quick_mode
        if last_mode in ["ติวละเอียด", "ฝึกทีละขั้น", "เฉลยไว"]:
            st.session_state.last_quick_mode = last_mode
        st.session_state.current_chat_id = str(chat_id) if chat_id else ""
        st.session_state.current_chat_dirty = dirty


def reset_current_chat():
    st.session_state.messages = []
    st.session_state.pending_prompt = ""
    st.session_state.weakness_counts = {}
    st.session_state.socratic_continue = False
    st.session_state.socratic_can_continue = False
    st.session_state.current_chat_id = ""
    st.session_state.current_chat_dirty = False
    st.session_state.worksheet_export_content = ""
    st.session_state.worksheet_export_name = ""
    st.session_state.worksheet_export_ready = False
    st.session_state.manual_weakness_text = ""
    save_store()


def archive_current_chat(mode_name: str):
    if not st.session_state.messages:
        return

    if st.session_state.current_chat_id and not st.session_state.current_chat_dirty:
        return

    first_user = next(
        (m.get("content", "") for m in st.session_state.messages if m.get("role") == "user"),
        "แชทคณิตศาสตร์"
    )
    title = clean_snippet(first_user, 50) or "แชทคณิตศาสตร์"

    chat_id = st.session_state.current_chat_id or f"chat_{int(time.time() * 1000)}"
    snapshot = {
        "id": chat_id,
        "title": title,
        "mode": mode_name,
        "messages": sanitize_messages_for_storage(st.session_state.messages),
        "weakness_counts": copy.deepcopy(st.session_state.weakness_counts),
        "updated_at": now_pretty(),
        "created_at": now_pretty(),
        "message_count": len(st.session_state.messages),
    }

    existing_idx = next(
        (idx for idx, item in enumerate(st.session_state.chat_history) if item.get("id") == chat_id),
        -1
    )
    if existing_idx >= 0:
        prev_created_at = st.session_state.chat_history[existing_idx].get("created_at", now_pretty())
        snapshot["created_at"] = prev_created_at
        st.session_state.chat_history[existing_idx] = snapshot
        if existing_idx != 0:
            moved = st.session_state.chat_history.pop(existing_idx)
            st.session_state.chat_history.insert(0, moved)
    else:
        st.session_state.chat_history.insert(0, snapshot)

    st.session_state.current_chat_id = chat_id
    st.session_state.current_chat_dirty = False
    st.session_state.chat_history = st.session_state.chat_history[:30]
    save_store()


def load_chat_snapshot(snapshot: dict):
    st.session_state.messages = copy.deepcopy(snapshot.get("messages", []))
    st.session_state.weakness_counts = copy.deepcopy(snapshot.get("weakness_counts", {}))
    st.session_state.pending_prompt = ""
    st.session_state.socratic_continue = False
    st.session_state.socratic_can_continue = False
    st.session_state.current_chat_id = str(snapshot.get("id", ""))
    st.session_state.current_chat_dirty = False
    mode_from_snapshot = snapshot.get("mode", "ติวละเอียด")
    if mode_from_snapshot in ["ติวละเอียด", "ฝึกทีละขั้น", "เฉลยไว"]:
        st.session_state.pending_quick_mode_restore = mode_from_snapshot
        st.session_state.pending_last_mode_restore = mode_from_snapshot
    save_store()


load_store_once()

# ─────────────────────────────────────────────
#  Handle selection query param
# ─────────────────────────────────────────────
sel_query = str(st.query_params.get("ask_sel", "")).strip()
if isinstance(st.query_params.get("ask_sel", ""), list):
    sel_query = st.query_params["ask_sel"][0]
if sel_query:
    st.session_state.pending_prompt = (
        f"ฉันคลุมข้อความนี้จากคำตอบ AI:\n\"{sel_query}\"\n\n"
        "ช่วยอธิบายส่วนนี้แบบเข้าใจง่าย พร้อมสูตรที่เกี่ยวข้องและตัวอย่างสั้น ๆ"
    )
    save_store()
    if "ask_sel" in st.query_params:
        del st.query_params["ask_sel"]
    st.rerun()

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    if st.session_state.pending_quick_mode_restore:
        st.session_state.quick_mode = st.session_state.pending_quick_mode_restore
        st.session_state.pending_quick_mode_restore = ""
    if st.session_state.pending_last_mode_restore:
        st.session_state.last_quick_mode = st.session_state.pending_last_mode_restore
        st.session_state.pending_last_mode_restore = ""

    st.markdown("### ⚙️ ตั้งค่าระบบ")

    API_KEY = st.text_input(
        "Groq API Key",
        type="password",
        placeholder="gsk_…",
        help="รับฟรีที่ console.groq.com",
    )

    st.markdown('<div class="section-label">โหมดการสอน</div>', unsafe_allow_html=True)
    quick_mode = st.radio(
        "",
        ["ติวละเอียด", "ฝึกทีละขั้น", "เฉลยไว"],
        horizontal=True,
        label_visibility="collapsed",
        key="quick_mode",
    )

    if st.session_state.last_quick_mode != quick_mode:
        archive_current_chat(st.session_state.last_quick_mode)
        reset_current_chat()
        st.session_state.last_quick_mode = quick_mode
        save_store()

    # Map quick mode → style/tutor_mode
    mode_map = {
        "ติวละเอียด": ("📝 สอนและอธิบายละเอียด", "โหมดปกติ"),
        "ฝึกทีละขั้น": ("📝 สอนและอธิบายละเอียด", "โหมดฝึกทีละขั้น (Socratic)"),
        "เฉลยไว":     ("⚡️ เฉลยอย่างเดียว",       "โหมดปกติ"),
    }
    response_style, tutor_mode = mode_map[quick_mode]

    # Defaults
    MODEL_NAME      = "qwen/qwen3-32b"
    learner_level   = "มหาวิทยาลัยปีต้น"
    explain_speed   = "พอดี"
    language_pref   = "ไทย+อังกฤษศัพท์สำคัญ"

    with st.expander("⚙️ ตั้งค่าขั้นสูง", expanded=False):
        MODEL_NAME = st.selectbox(
            "โมเดล AI",
            [
                "qwen/qwen3-32b",
                "deepseek-r1-distill-llama-70b",
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
            ],
            index=0,
        )
        if st.checkbox("ปรับค่าการสอนเอง", value=False):
            response_style = st.selectbox(
                "รูปแบบการตอบ",
                ["📝 สอนและอธิบายละเอียด", "⚡️ เฉลยอย่างเดียว"],
            )
            tutor_mode = st.selectbox(
                "โหมดติวเตอร์",
                ["โหมดปกติ", "โหมดฝึกทีละขั้น (Socratic)"],
            )
            learner_level = st.selectbox(
                "ระดับผู้เรียน",
                ["ม.ต้น", "ม.ปลาย", "มหาวิทยาลัยปีต้น", "มหาวิทยาลัยปีสูง"],
            )
            explain_speed = st.selectbox(
                "ความเร็วอธิบาย",
                ["ช้าและละเอียด", "พอดี", "กระชับเร็ว"],
            )
            language_pref = st.selectbox(
                "ภาษา",
                ["ไทย", "ไทย+อังกฤษศัพท์สำคัญ", "English"],
            )

        st.session_state.enable_python_calc = st.checkbox(
            "คำนวณแม่นยำด้วย Python (Beta)",
            value=st.session_state.enable_python_calc,
            help="ถ้า AI ส่งโค้ด Python สำหรับคำนวณ ระบบจะรันและแสดงผลลัพธ์จริง",
        )

    model_short = MODEL_NAME.split("/")[-1].split("-distill")[0]
    st.markdown(
        f'<div class="header-meta" style="margin:4px 0 8px;">'
        f'<span class="status-dot"></span>'
        f'<span class="model-chip">✦ {model_short}</span></div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Export current chat
    st.markdown('<div class="section-label">⬇️ ส่งออกแชทปัจจุบัน</div>', unsafe_allow_html=True)
    if st.session_state.messages:
        export_html = build_chat_export_html(st.session_state.messages, clean_content_for_export)
        export_md = build_chat_export_markdown(st.session_state.messages)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cexp1, cexp2 = st.columns(2)
        cexp1.download_button(
            "HTML",
            data=export_html,
            file_name=f"math_tutor_chat_{stamp}.html",
            mime="text/html",
            use_container_width=True,
        )
        cexp2.download_button(
            "Markdown",
            data=export_md,
            file_name=f"math_tutor_chat_{stamp}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    else:
        st.caption("ยังไม่มีข้อความสำหรับส่งออก")

    st.divider()

    # ── Chat History
    with st.expander("🕘 ประวัติการถาม", expanded=False):
        col_new, col_clear = st.columns(2)
        if col_new.button("＋ แชทใหม่", use_container_width=True):
            archive_current_chat(st.session_state.last_quick_mode)
            reset_current_chat()
            st.rerun()
        if col_clear.button("ล้างประวัติ", use_container_width=True):
            st.session_state.chat_history = []
            save_store()
            st.rerun()

        st.caption(f"ประวัติทั้งหมด: {len(st.session_state.chat_history)} แชท")

        if not st.session_state.chat_history:
            st.caption("ยังไม่มีประวัติแชท")
        else:
            for i, snap in enumerate(st.session_state.chat_history[:12]):
                col_t, col_o, col_d = st.columns([2.8, 1, 1])
                col_t.markdown(f"**{snap.get('title', 'แชทคณิตศาสตร์')}**")
                col_t.caption(
                    f"{snap.get('mode', '-')} · {snap.get('updated_at', '-')} · {snap.get('message_count', len(snap.get('messages', [])))} ข้อความ"
                )
                if col_o.button("เปิด", key=f"open_hist_{snap.get('id', i)}"):
                    archive_current_chat(st.session_state.last_quick_mode)
                    load_chat_snapshot(snap)
                    st.rerun()
                if col_d.button("ลบ", key=f"del_hist_{snap.get('id', i)}"):
                    deleted_id = snap.get("id")
                    st.session_state.chat_history = [
                        c for c in st.session_state.chat_history if c.get("id") != deleted_id
                    ]
                    if st.session_state.current_chat_id == deleted_id:
                        st.session_state.current_chat_id = ""
                        st.session_state.current_chat_dirty = bool(st.session_state.messages)
                    save_store()
                    st.rerun()

    st.divider()

    # ── File Upload
    st.markdown('<div class="section-label">📎 แนบไฟล์</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "PDF, TXT หรือรูปโจทย์",
        type=["pdf", "txt", "png", "jpg", "jpeg"],
        label_visibility="collapsed",
    )

    file_content  = ""
    uploaded_img  = None
    base64_image  = None

    if uploaded_file:
        ftype = uploaded_file.type
        if ftype.startswith("image/"):
            uploaded_img = Image.open(uploaded_file)
            base64_image = encode_image(uploaded_img)
            st.image(uploaded_img, caption="📸 รูปที่อัปโหลด", use_container_width=True)
            st.success("✅ โหลดรูปสำเร็จ")

            if st.button("🔍 วิเคราะห์สูตรจากรูปนี้ (แบบง่าย)", use_container_width=True):
                if not API_KEY.strip():
                    st.warning("กรุณาใส่ Groq API Key ก่อน")
                else:
                    with st.spinner("🔎 กำลังอ่านข้อความ/สมการจากรูป..."):
                        analysis_text, analysis_err = extract_math_latex_from_image(
                            api_key=API_KEY.strip(),
                            image_b64=base64_image,
                            preferred_model=MODEL_NAME,
                            prompt_hint="โฟกัสการอ่านให้ชัด แล้วส่งข้อความและ LaTeX ที่ถูกต้อง",
                        )

                    if analysis_text:
                        st.session_state.pending_prompt = (
                            f"ฉันแนบรูปโจทย์นี้มา:\n{analysis_text}\n\n"
                            "ช่วยอธิบายให้เข้าใจง่ายและเชื่อมกับวิธีทำในข้อสอบ"
                        )
                        save_store()
                        st.rerun()
                    else:
                        st.error(analysis_err or "ยังวิเคราะห์ภาพไม่ได้ ลองใหม่อีกครั้ง")

            cropper_fn = get_cropper_func()
            if cropper_fn is not None:
                with st.expander("โหมดขั้นสูง: ครอปเฉพาะส่วน", expanded=False):
                    st.caption("ลากกรอบเฉพาะสูตรที่สงสัย แล้วกดปุ่มวิเคราะห์")
                    cropped_img = cropper_fn(
                        uploaded_img,
                        realtime_update=True,
                        return_type="image",
                        box_color="#3b82f6",
                        aspect_ratio=None,
                        key="formula_cropper",
                    )
                    if cropped_img is not None:
                        st.image(cropped_img, caption="🧩 ส่วนที่ครอป", use_container_width=True)

                        if st.button("🔍 วิเคราะห์จากส่วนที่ครอป", use_container_width=True):
                            if not API_KEY.strip():
                                st.warning("กรุณาใส่ Groq API Key ก่อน")
                            else:
                                crop_b64 = encode_image(cropped_img)
                                with st.spinner("🔎 กำลังอ่านข้อความ/สมการจากภาพที่ครอป..."):
                                    analysis_text, analysis_err = extract_math_latex_from_image(
                                        api_key=API_KEY.strip(),
                                        image_b64=crop_b64,
                                        preferred_model=MODEL_NAME,
                                        prompt_hint="ภาพนี้เป็นส่วนที่ครอป ให้เน้นอ่านข้อความ/สมการตามที่เห็นเท่านั้น",
                                    )

                                if analysis_text:
                                    st.session_state.pending_prompt = (
                                        f"ฉันครอปส่วนนี้มา:\n{analysis_text}\n\n"
                                        "ช่วยอธิบายเพิ่มว่ามาจากสูตรไหน และเชื่อมกับขั้นตอนในโจทย์ยังไง"
                                    )
                                    save_store()
                                    st.rerun()
                                else:
                                    st.error(analysis_err or "ยังวิเคราะห์ภาพครอปไม่ได้ ลองครอปให้ชัดขึ้น")
            else:
                st.caption("หมายเหตุ: โหมดครอปขั้นสูงต้องใช้แพ็กเกจ streamlit-cropper")
        elif ftype == "application/pdf":
            try:
                reader = PyPDF2.PdfReader(uploaded_file)
                pages  = [p.extract_text() or "" for p in reader.pages]
                file_content = "\n".join(pages)
                st.success(f"✅ PDF {len(reader.pages)} หน้า (~{count_tokens_approx(file_content):,} tokens)")
            except Exception as e:
                st.error(f"อ่าน PDF ไม่ได้: {e}")
        else:
            try:
                file_content = uploaded_file.getvalue().decode("utf-8")
                st.success(f"✅ ข้อความ (~{count_tokens_approx(file_content):,} tokens)")
            except:
                st.error("อ่านไฟล์ไม่ได้")

    st.divider()

    # ── Stats & Weakness
    total_msgs  = len(st.session_state.messages)
    total_chars = sum(len(str(m.get("content", ""))) for m in st.session_state.messages)

    with st.expander("📊 สถิติการเรียน", expanded=False):
        c1, c2 = st.columns(2)
        c1.metric("💬 ข้อความ", total_msgs)
        c2.metric("📊 Tokens", f"{count_tokens_approx(total_chars*4):,}")

        if st.session_state.weakness_counts:
            st.markdown('<div class="section-label">📌 หัวข้อที่ควรทบทวน</div>', unsafe_allow_html=True)
            topic_prompts = {
                "พีชคณิต":    "ออกแบบแบบฝึกหัดพีชคณิต 3 ข้อ ไล่จากง่ายไปยาก พร้อมเฉลยทีละขั้น",
                "แคลคูลัส":  "ทบทวนแคลคูลัสหัวข้ออนุพันธ์/อินทิเกรต พร้อมโจทย์ฝึก 2 ข้อ",
                "ตรีโกณมิติ":"สรุปตรีโกณมิติที่มักสับสน พร้อมตัวอย่างโจทย์ 2 ข้อ",
                "เรขาคณิต":  "สรุปสูตรเรขาคณิตที่ต้องจำ แล้วทดสอบด้วยโจทย์ 2 ข้อ",
                "สถิติ":     "ติวสถิติพื้นฐานแบบเข้าใจง่าย พร้อมโจทย์ฝึก 2 ข้อ",
                "เมทริกซ์":  "สอนเมทริกซ์ทีละขั้น แล้วให้แบบฝึกหัดพร้อมตรวจ",
            }
            tops = sorted(
                st.session_state.weakness_counts.items(),
                key=lambda x: x[1], reverse=True
            )[:3]
            for topic, cnt in tops:
                col_t, col_b = st.columns([2, 1])
                col_t.markdown(f'<span class="topic-pill">{topic}</span>', unsafe_allow_html=True)
                col_t.caption(f"{cnt} ครั้ง")
                if col_b.button("ฝึก", key=f"prac_{topic}"):
                    st.session_state.pending_prompt = topic_prompts.get(
                        topic, f"ช่วยสอนเรื่อง {topic} แบบติวเตอร์ส่วนตัว"
                    )
                    st.rerun()

        render_worksheet_generator_ui(
            api_key=API_KEY,
            model_name=MODEL_NAME,
            learner_level=learner_level,
            language_pref=language_pref,
        )

    if st.button("🗑️ ล้างการสนทนา", use_container_width=True):
        reset_current_chat()
        st.rerun()

    st.caption("🔒 API Key ไม่ถูกบันทึก")

# ─────────────────────────────────────────────
#  Header
# ─────────────────────────────────────────────
col_t, col_m = st.columns([5, 1])
with col_t:
    st.title("∑ Math AI Tutor")
    st.caption("ติวเตอร์คณิตศาสตร์ส่วนตัว — อธิบายครบ ทุกขั้นตอน")

# ─────────────────────────────────────────────
#  Display Chat History
# ─────────────────────────────────────────────
for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if "image_show" in message:
            st.image(message["image_show"], width=260)

        content = strip_internal_tags(message["content"])
        is_quick_solve_msg = message.get("response_style") == "⚡️ เฉลยอย่างเดียว"
        decorate_final = not is_quick_solve_msg

        if message["role"] == "assistant" and "</think>" in str(content):
            parts       = str(content).split("</think>")
            think_text  = parts[0].replace("<think>", "").strip()
            answer_text = parts[1].strip()
            with st.expander("💡 กระบวนการคิดของ AI", expanded=False):
                st.markdown(
                    f'<div class="think-stream">{think_text}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown(beautify_answer_text(answer_text, decorate_final=decorate_final), unsafe_allow_html=True)
        else:
            st.markdown(beautify_answer_text(str(content), decorate_final=decorate_final), unsafe_allow_html=True)

        if "plot" in message:
            st.pyplot(message["plot"])

        if message.get("python_result"):
            st.markdown(
                f'<div class="final-answer"><strong>🧮 ผลคำนวณจาก Python</strong><br>{message.get("python_result")}</div>',
                unsafe_allow_html=True,
            )

        if message["role"] == "user":
            if st.button("✏️ แก้ข้อความนี้", key=f"edit_msg_{msg_idx}", use_container_width=False):
                st.session_state.edit_message_index = msg_idx
                st.session_state.edit_message_text = str(message.get("content", ""))
                st.rerun()

        # ── Persistent continue button on latest assistant message (Socratic only)
        if (
            message["role"] == "assistant"
            and "Socratic" in tutor_mode
            and msg_idx == len(st.session_state.messages) - 1
            and st.session_state.socratic_can_continue
        ):
            if st.button(
                "➡️  ไปต่อ — สอนขั้นถัดไป",
                key=f"soc_cont_hist_{msg_idx}",
                use_container_width=False,
            ):
                st.session_state.pending_prompt = "ไปต่อ"
                st.session_state.socratic_continue = True
                st.rerun()

# ─────────────────────────────────────────────
#  Chat Input
# ─────────────────────────────────────────────
if not (0 <= st.session_state.edit_message_index < len(st.session_state.messages)):
    st.session_state.edit_message_index = -1

if st.session_state.edit_message_index >= 0:
    st.markdown("### ✏️ แก้โจทย์ที่ส่งไปแล้ว")
    st.caption("บันทึกแล้วระบบจะลบข้อความถัดจากจุดนั้น และสร้างคำตอบใหม่จากข้อความที่แก้")
    st.text_area(
        "แก้ข้อความ",
        key="edit_message_text",
        height=100,
        label_visibility="collapsed",
    )
    ce1, ce2 = st.columns(2)
    if ce1.button("บันทึกและสร้างคำตอบใหม่", use_container_width=True):
        edited = st.session_state.edit_message_text.strip()
        if not edited:
            st.warning("ข้อความแก้ไขว่างไม่ได้")
        else:
            cut_idx = st.session_state.edit_message_index
            st.session_state.messages = st.session_state.messages[:cut_idx]
            st.session_state.pending_prompt = edited
            st.session_state.edit_message_index = -1
            st.session_state.edit_message_text = ""
            st.session_state.current_chat_dirty = True
            save_store()
            st.rerun()
    if ce2.button("ยกเลิกการแก้ไข", use_container_width=True):
        st.session_state.edit_message_index = -1
        st.session_state.edit_message_text = ""
        st.rerun()

typed_prompt  = st.chat_input("✏️  พิมพ์โจทย์หรือคำถามคณิตศาสตร์…")
queued_prompt = st.session_state.pending_prompt.strip()
prompt        = typed_prompt if typed_prompt else (queued_prompt if queued_prompt else "")

if prompt:
    prompt_lower = str(prompt).lower()
    is_continue_request = "ไปต่อ" in prompt_lower
    is_full_solution_request = "เฉลยเต็ม" in prompt_lower

    if queued_prompt and not typed_prompt:
        st.session_state.pending_prompt = ""

    if "Socratic" in tutor_mode:
        if is_continue_request:
            if not st.session_state.socratic_can_continue:
                st.info("โจทย์นี้จบแล้วครับ ให้พิมพ์โจทย์ใหม่เพื่อเริ่มรอบใหม่")
                st.stop()
            st.session_state.socratic_continue = True
        else:
            st.session_state.socratic_continue = False
            st.session_state.socratic_can_continue = True

    if not API_KEY.strip():
        st.error("⚠️ กรุณาใส่ Groq API Key ที่แถบด้านซ้ายก่อนครับ")
        st.stop()

    update_weakness(prompt)

    # Save & display user message
    user_msg: dict = {"role": "user", "content": prompt}
    if uploaded_img:
        user_msg["image_show"] = uploaded_img
    st.session_state.messages.append(user_msg)
    st.session_state.current_chat_dirty = True
    save_store()

    with st.chat_message("user"):
        if uploaded_img:
            st.image(uploaded_img, width=260)
        st.markdown(prompt)

    # ── Build System Prompt
    if "Socratic" in tutor_mode:
        overview_only_instruction = (
            "\n7. ถ้ายังไม่ใช่คำสั่ง 'ไปต่อ' หรือ 'เฉลยเต็ม' ให้ตอบแบบภาพรวมเท่านั้น:"
            " บอกจำนวนขั้นตอนและสิ่งที่จะทำในแต่ละขั้นแบบสั้น ๆ ห้ามคำนวณละเอียด"
            " และห้ามเฉลยผลลัพธ์สุดท้าย"
            "\n8. ห้ามแสดงคำตอบสุดท้าย ห้ามใช้ \\boxed{...} และห้ามสรุปเป็น = ... + C ในรอบนี้"
            "\n9. ตอนท้ายให้ปิดด้วยประโยค: 'พร้อมแล้วกดปุ่ม ➡️ ไปต่อ'"
            " และใส่ [[STEP_STATUS:CONTINUE]]"
        )
        continue_step_instruction = (
            "\n7. เมื่อได้รับคำสั่ง 'ไปต่อ' ให้สอนเฉพาะขั้นถัดไป 1 ขั้นเท่านั้น"
            " และจบด้วยประโยค: 'พร้อมแล้วกดปุ่ม ➡️ ไปต่อ'"
            "\n8. ถ้ายังไม่จบข้อ ให้ใส่ [[STEP_STATUS:CONTINUE]] ต่อท้ายคำตอบ"
            "\n9. ถ้าจบข้อแล้วหรือให้คำตอบสุดท้าย ให้ใส่ [[STEP_STATUS:DONE]] ต่อท้ายคำตอบ"
        )

        stage_rule = continue_step_instruction if (is_continue_request or st.session_state.socratic_continue) else overview_only_instruction
        should_force_overview = not is_continue_request and not is_full_solution_request and not st.session_state.socratic_continue

        base_sys = (
            "คุณคือติวเตอร์คณิตศาสตร์ส่วนตัว (โหมดฝึกทีละขั้น)\n"
            "กฎเหล็ก:\n"
            "1. ห้ามเฉลยรวดเดียวตั้งแต่ต้น\n"
            "2. ถามคำถามชี้นำทีละขั้น แล้วรอผู้เรียนตอบ\n"
            "3. ตรวจคำตอบผู้เรียนอย่างตรงจุด\n"
            "4. เฉลยเต็มได้เมื่อผู้เรียนพิมพ์ 'เฉลยเต็ม'\n"
            "5. เมื่อผู้เรียนพิมพ์ 'ไปต่อ' ให้สอนเพียง 1 ขั้นถัดไป แล้วถามกลับ\n"
            "6. ทุกสมการอยู่ใน LaTeX\n"
            "7. ก่อนส่งคำตอบ ตรวจว่าวงเล็บ (), {}, และรูปแบบ LaTeX ปิดครบ ห้ามส่งสมการที่ขาดท้าย\n"
            "8. ถ้าโจทย์เป็น Integration by Parts ต้องระบุให้สอดคล้องว่า ∫u dv = uv - ∫v du และ u,dv,du,v ต้องสัมพันธ์กัน"
            f"{stage_rule}"
        )
    elif "อธิบายละเอียด" in response_style:
        base_sys = (
            "คุณคืออาจารย์คณิตศาสตร์ (โหมดอธิบายละเอียด)\n"
            "กฎเหล็ก:\n"
            "1. บอกเหตุผลทุกครั้งว่า 'ทำไมถึงใช้สูตรนี้'\n"
            "2. โครงสร้าง: **1. วิเคราะห์โจทย์** → **2. วิธีทำ** → **3. สรุปคำตอบ**\n"
            "3. บังคับใช้ LaTeX ทุกสมการ\n"
            "4. ตอบเฉพาะข้อที่ผู้ใช้สั่ง\n"
            "5. ตรวจให้แน่ใจว่าสมการปิดวงเล็บครบก่อนส่ง"
        )
    else:
        base_sys = (
            "คุณคือเครื่องคำนวณคณิตศาสตร์ (โหมดเฉลยอย่างเดียว)\n"
            "กฎเหล็ก:\n"
            "1. ห้ามคำบรรยายภาษาไทย ยกเว้น 'คำตอบสุดท้าย:'\n"
            "2. แสดงเฉพาะบรรทัดสมการเรียงลงมาจนจบ\n"
            "3. ใช้ LaTeX Aligned: $$ \\begin{aligned} … \\end{aligned} $$\n"
            "4. บรรทัดล่างสุด: **คำตอบสุดท้าย:** ตามด้วยสมการ\n"
            "5. ห้ามส่งสมการที่ไม่จบหรือวงเล็บไม่ครบ"
        )
        should_force_overview = False

    profile   = build_profile_prompt(learner_level, explain_speed, language_pref, tutor_mode)
    empathy_prompt = build_empathy_prompt(response_style != "⚡️ เฉลยอย่างเดียว")
    calc_instruction = ""
    if st.session_state.enable_python_calc:
        calc_instruction = (
            "\n\nกฎคำนวณแม่นยำ:\n"
            "- ถ้าต้องคำนวณตัวเลขที่ซับซ้อน ให้แนบโค้ด ```python``` ที่รันได้\n"
            "- ให้กำหนด result และ print(result)"
        )
    sys_prompt = f"{base_sys}\n\n{profile}{empathy_prompt}{calc_instruction}"

    is_deepseek = "deepseek" in MODEL_NAME.lower()
    is_vision   = "vision"   in MODEL_NAME.lower()

    # Build messages list for API
    messages_for_ai: list = []
    if not is_deepseek:
        messages_for_ai.append({"role": "system", "content": sys_prompt})

    for i, m in enumerate(st.session_state.messages):
        role         = m["role"]
        content_text = str(m["content"])

        if is_deepseek and i == 0 and role == "user":
            content_text = f"[คำสั่งระบบ: {sys_prompt}]\n\n" + content_text

        if i == len(st.session_state.messages) - 1 and role == "user":
            if file_content:
                content_text += f"\n\n[ข้อมูลจากไฟล์]:\n{file_content[:4000]}"
            if base64_image:
                if is_vision:
                    messages_for_ai.append({
                        "role": role,
                        "content": [
                            {"type": "text",      "text": content_text},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        ],
                    })
                    continue
                else:
                    extracted_text, ocr_err = extract_math_latex_from_image(
                        api_key=API_KEY.strip(),
                        image_b64=base64_image,
                        preferred_model=MODEL_NAME,
                        prompt_hint=content_text,
                    )
                    if ocr_err:
                        st.warning(ocr_err)

                    if extracted_text:
                        content_text += f"\n\n[ข้อความที่สกัดได้จากรูปภาพ]:\n{extracted_text[:6000]}"

        messages_for_ai.append({"role": role, "content": content_text})

    # ── Stream response
    with st.chat_message("assistant"):
        try:
            client        = Groq(api_key=API_KEY.strip())
            full_response = ""
            is_thinking   = False
            ans_ph        = st.empty()
            status_box    = None
            start_time    = time.time()

            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages_for_ai,
                stream=True,
                max_tokens=8192,
                temperature=0.2,
            )

            for chunk in stream:
                txt            = chunk.choices[0].delta.content or ""
                full_response += txt

                if "<think>" in full_response and "</think>" not in full_response:
                    if not is_thinking:
                        is_thinking = True
                        status_box  = st.status("🧠 กำลังวิเคราะห์…", expanded=True)
                        think_ph    = status_box.empty()
                    think_raw = full_response.split("<think>")[-1]
                    think_ph.markdown(
                        f'<div class="think-stream">{think_raw} ▌</div>',
                        unsafe_allow_html=True,
                    )
                elif "</think>" in full_response:
                    if is_thinking:
                        is_thinking = False
                        if status_box:
                            status_box.update(label="✅ วิเคราะห์เสร็จ", state="complete", expanded=False)
                    ans_ph.markdown(
                        beautify_answer_text(
                            full_response.split("</think>")[-1],
                            decorate_final=(response_style != "⚡️ เฉลยอย่างเดียว")
                        ) + " ▌",
                        unsafe_allow_html=True,
                    )
                else:
                    ans_ph.markdown(
                        beautify_answer_text(
                            full_response,
                            decorate_final=(response_style != "⚡️ เฉลยอย่างเดียว")
                        ) + " ▌",
                        unsafe_allow_html=True,
                    )

            # Final clean render
            final_answer_raw = (
                full_response.split("</think>")[-1]
                if "</think>" in full_response
                else full_response
            )

            if "Socratic" in tutor_mode and should_force_overview and violates_socratic_overview(final_answer_raw):
                final_answer_raw = build_socratic_overview_fallback()

            is_done_now = False
            if "Socratic" in tutor_mode:
                is_done_now = is_socratic_done(final_answer_raw, force_done=is_full_solution_request)
                st.session_state.socratic_can_continue = not is_done_now

            final_answer = strip_internal_tags(final_answer_raw)
            ans_ph.markdown(
                beautify_answer_text(
                    final_answer,
                    decorate_final=(response_style != "⚡️ เฉลยอย่างเดียว")
                ).strip(),
                unsafe_allow_html=True,
            )

            # ── Socratic continue button (after streaming)
            if "Socratic" in tutor_mode:
                if st.session_state.socratic_can_continue and st.button(
                    "➡️  ไปต่อ — สอนขั้นถัดไป",
                    key="soc_cont_stream",
                    use_container_width=False,
                ):
                    st.session_state.pending_prompt = "ไปต่อ"
                    st.session_state.socratic_continue = True
                    st.rerun()

            # ── Auto-plot graph if code block exists
            plot_fig = None
            python_result = None
            code_m   = re.search(r'```python\n(.*?)```', full_response, re.DOTALL)
            if code_m:
                code_text = code_m.group(1)
                if "plt" in code_text or "ax" in code_text:
                    try:
                        fig, ax = plt.subplots(facecolor='none')
                        ax.set_facecolor('#0d1117')
                        for spine in ax.spines.values():
                            spine.set_color('#334155')
                        ax.tick_params(colors='#94a3b8')
                        exec(
                            f"import numpy as np\n{code_text}",
                            {"plt": plt, "np": np, "ax": ax},
                            {},
                        )
                        st.pyplot(fig)
                        plot_fig = fig
                    except:
                        pass
                elif st.session_state.enable_python_calc:
                    ok, py_out = run_python_code_capture(code_text)
                    if ok:
                        python_result = py_out
                        st.markdown(
                            f'<div class="final-answer"><strong>🧮 ผลคำนวณจาก Python</strong><br>{py_out}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption(f"Python execution error: {py_out}")

            elapsed = time.time() - start_time
            st.caption(f"⚡ {elapsed:.2f}s  ·  {model_short}  ·  {'Socratic' if 'Socratic' in tutor_mode else response_style.split()[0]}")

            # Save response
            res_msg: dict = {
                "role": "assistant",
                "content": strip_internal_tags(full_response),
                "response_style": response_style,
                "tutor_mode": tutor_mode,
            }
            if plot_fig:
                res_msg["plot"] = plot_fig
            if python_result:
                res_msg["python_result"] = python_result
            st.session_state.messages.append(res_msg)
            st.session_state.current_chat_dirty = True
            save_store()

        except Exception as e:
            st.error(f"🚨 เกิดข้อผิดพลาด: {e}")
            st.info("💡 ตรวจสอบ API Key หรือชื่อโมเดลครับ")