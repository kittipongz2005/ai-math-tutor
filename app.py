import streamlit as st
import PyPDF2
import time
import io
import re
import base64
import copy
import json
from datetime import datetime
from pathlib import Path
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from groq import Groq

STORE_PATH = Path(".math_tutor_store.json")

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
#  Global CSS – Premium Dark Design
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');

:root {
    --bg-base:       #080c14;
    --bg-surface:    #0e1520;
    --bg-elevated:   #131d2e;
    --bg-overlay:    #182234;
    --accent-blue:   #3b82f6;
    --accent-cyan:   #06b6d4;
    --accent-violet: #8b5cf6;
    --accent-green:  #10b981;
    --accent-amber:  #f59e0b;
    --text-primary:  #f1f5f9;
    --text-secondary:#94a3b8;
    --text-muted:    #475569;
    --border-dim:    rgba(148,163,184,0.08);
    --border-glow:   rgba(59,130,246,0.35);
    --glow-blue:     0 0 30px rgba(59,130,246,0.15);
    --radius-sm:     8px;
    --radius-md:     12px;
    --radius-lg:     18px;
    --transition:    all 0.2s cubic-bezier(0.4,0,0.2,1);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; }

html, body, [class*="css"] {
    font-family: 'DM Sans', 'Noto Sans Thai', sans-serif;
}

/* ── BACKGROUND ── */
.stApp {
    background: var(--bg-base);
    background-image:
        radial-gradient(ellipse 80% 50% at 20% -10%, rgba(59,130,246,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 110%, rgba(139,92,246,0.05) 0%, transparent 60%);
    min-height: 100vh;
}

/* ── MAIN CONTENT ── */
.block-container {
    padding: 1.75rem 2rem 4rem !important;
    max-width: 860px !important;
}

/* ── HEADINGS ── */
h1 {
    font-family: 'DM Sans', 'Noto Sans Thai', sans-serif !important;
    font-size: 1.65rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.6px !important;
    background: linear-gradient(135deg, #60a5fa 0%, #38bdf8 45%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2 !important;
    margin-bottom: 0.15rem !important;
}

h2, h3 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: -0.3px !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border-dim) !important;
    box-shadow: 4px 0 24px rgba(0,0,0,0.3) !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1.1rem 2rem !important;
}

[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--text-secondary) !important;
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.2px !important;
    margin: 0 0 0.6rem !important;
}

/* ── INPUTS ── */
[data-testid="stTextInput"] input {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
    transition: var(--transition) !important;
}

[data-testid="stTextInput"] input:focus {
    border-color: var(--accent-blue) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
    outline: none !important;
}

[data-testid="stTextInput"] input::placeholder { color: var(--text-muted) !important; }

/* ── SELECTBOX ── */
[data-testid="stSelectbox"] > div > div {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
}

/* ── RADIO ── */
[data-testid="stRadio"] label {
    color: var(--text-secondary) !important;
    font-size: 0.82rem !important;
}

[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.82rem !important;
    color: var(--text-secondary) !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-cyan) 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', 'Noto Sans Thai', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    letter-spacing: 0.2px !important;
    padding: 0.5rem 1.1rem !important;
    transition: var(--transition) !important;
    box-shadow: 0 2px 12px rgba(59,130,246,0.2) !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(59,130,246,0.35) !important;
}

.stButton > button:active { transform: translateY(0) !important; }

/* Secondary / ghost button via key prefix */
.btn-secondary .stButton > button {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-dim) !important;
    color: var(--text-secondary) !important;
    box-shadow: none !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: rgba(59,130,246,0.03) !important;
    border: 1.5px dashed rgba(59,130,246,0.25) !important;
    border-radius: var(--radius-md) !important;
    transition: var(--transition) !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(59,130,246,0.55) !important;
    background: rgba(59,130,246,0.06) !important;
}

/* ── CHAT MESSAGES ── */
[data-testid="stChatMessage"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: var(--radius-lg) !important;
    padding: 1rem 1.3rem !important;
    margin-bottom: 0.6rem !important;
    backdrop-filter: blur(8px) !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: rgba(59,130,246,0.06) !important;
    border-color: rgba(59,130,246,0.14) !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: rgba(139,92,246,0.05) !important;
    border-color: rgba(139,92,246,0.12) !important;
}

/* ── CHAT INPUT ── */
[data-testid="stChatInput"] {
    background: var(--bg-elevated) !important;
    border: 1.5px solid rgba(59,130,246,0.22) !important;
    border-radius: var(--radius-md) !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: rgba(59,130,246,0.65) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.08) !important;
}

[data-testid="stChatInput"] textarea {
    color: var(--text-primary) !important;
    font-family: 'DM Sans', 'Noto Sans Thai', sans-serif !important;
    font-size: 0.9rem !important;
}

/* ── TEXT ── */
p, li, span, label { color: var(--text-secondary) !important; }
strong, b           { color: var(--text-primary) !important; }

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    color: var(--text-secondary) !important;
    line-height: 1.85 !important;
    font-size: 0.92rem !important;
}

code {
    color: var(--accent-cyan) !important;
    background: rgba(6,182,212,0.08) !important;
    border: 1px solid rgba(6,182,212,0.18) !important;
    border-radius: 5px !important;
    padding: 1px 6px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.82rem !important;
}

/* ── MATH BLOCKS ── */
.katex-display {
    background: rgba(59,130,246,0.05);
    border: 1px solid rgba(59,130,246,0.18);
    border-left: 3px solid var(--accent-blue);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    padding: 10px 16px;
    margin: 0.7rem 0;
    overflow-x: auto;
}

/* ── FINAL ANSWER BOX ── */
.final-answer {
    background: linear-gradient(135deg, rgba(16,185,129,0.08) 0%, rgba(6,182,212,0.05) 100%);
    border: 1px solid rgba(16,185,129,0.28);
    border-left: 3px solid var(--accent-green);
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
    padding: 12px 16px;
    margin-top: 1rem;
}

.final-answer strong { color: var(--accent-green) !important; }

/* ── EXPANDER (Thinking) ── */
[data-testid="stExpander"] {
    background: rgba(245,158,11,0.04) !important;
    border: 1px solid rgba(245,158,11,0.18) !important;
    border-radius: var(--radius-md) !important;
    overflow: hidden !important;
}

[data-testid="stExpander"] summary {
    color: var(--accent-amber) !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
}

/* ── STATUS ── */
[data-testid="stStatus"] {
    background: rgba(59,130,246,0.05) !important;
    border: 1px solid rgba(59,130,246,0.18) !important;
    border-radius: var(--radius-md) !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
    background: var(--bg-overlay) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: var(--radius-sm) !important;
    padding: 0.5rem 0.75rem !important;
}

[data-testid="stMetric"] label { color: var(--text-muted) !important; font-size: 0.72rem !important; }
[data-testid="stMetricValue"] { color: var(--text-primary) !important; font-size: 1.1rem !important; }

/* ── ALERTS ── */
[data-testid="stAlert"] {
    border-radius: var(--radius-md) !important;
    border-left-width: 3px !important;
    background: var(--bg-elevated) !important;
}

/* ── DIVIDER ── */
hr { border-color: var(--border-dim) !important; margin: 0.9rem 0 !important; }

/* ── CAPTION ── */
.stCaption, [data-testid="stCaptionContainer"] p {
    color: var(--text-muted) !important;
    font-size: 0.72rem !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(59,130,246,0.25);
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(59,130,246,0.5); }

/* ── IMAGES ── */
img { border-radius: var(--radius-sm) !important; }

/* ── INLINE SELECTION BUTTON ── */
#sel-ask-btn {
    position: fixed;
    z-index: 9999;
    display: none;
    padding: 6px 14px;
    font-size: 0.78rem;
    font-weight: 700;
    color: #fff;
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
    border: none;
    border-radius: 999px;
    cursor: pointer;
    box-shadow: 0 8px 20px rgba(59,130,246,0.4);
    backdrop-filter: blur(8px);
    transition: var(--transition);
}
#sel-ask-btn:hover { transform: translateY(-1px); box-shadow: 0 12px 28px rgba(59,130,246,0.5); }

/* ── CONTINUE BUTTON (Socratic) ── */
.socratic-continue-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 0.85rem;
    padding: 7px 18px;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-primary);
    background: var(--bg-overlay);
    border: 1px solid rgba(139,92,246,0.3);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: var(--transition);
    text-decoration: none;
}
.socratic-continue-btn:hover {
    border-color: var(--accent-violet);
    background: rgba(139,92,246,0.12);
    box-shadow: 0 4px 14px rgba(139,92,246,0.2);
}

/* ── THINKING STREAM ── */
.think-stream {
    font-family: 'DM Mono', monospace;
    font-size: 0.78rem;
    color: var(--text-muted);
    line-height: 1.8;
}

/* ── TOPIC BADGE ── */
.topic-pill {
    display: inline-block;
    padding: 2px 10px;
    background: rgba(59,130,246,0.1);
    border: 1px solid rgba(59,130,246,0.2);
    border-radius: 999px;
    font-size: 0.7rem;
    color: var(--accent-cyan);
    margin: 2px 2px;
}

/* ── HEADER META ── */
.header-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 2px;
}
.model-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 2px 10px;
    background: rgba(139,92,246,0.08);
    border: 1px solid rgba(139,92,246,0.2);
    border-radius: 999px;
    font-size: 0.7rem;
    color: #a78bfa;
    font-weight: 500;
}
.status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--accent-green);
    box-shadow: 0 0 6px var(--accent-green);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.6; transform: scale(0.85); }
}

/* ── SECTION LABELS ── */
.section-label {
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.1px;
    color: var(--text-muted);
    margin: 1rem 0 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── KaTeX math rendering
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body,{
        delimiters:[
            {left:'$$',right:'$$',display:true},
            {left:'$',right:'$',display:false}
        ],
        throwOnError:false
    });"></script>
""", unsafe_allow_html=True)

# ── Text-selection "Ask" floating button
st.markdown("""
<button id="sel-ask-btn">💬 ถามเรื่องนี้</button>
<script>
(function(){
    if(window.__selAskInit__) return;
    window.__selAskInit__ = true;
    const btn = document.getElementById('sel-ask-btn');
    let sel = '';
    document.addEventListener('mousedown', ()=> btn.style.display='none');
    document.addEventListener('mouseup', e=>{
        const s = (window.getSelection()||'').toString().trim();
        if(!s || s.length < 3){ btn.style.display='none'; return; }
        sel = s.slice(0,500);
        btn.style.left = Math.min(e.clientX+8, window.innerWidth-190)+'px';
        btn.style.top  = Math.max(e.clientY-44, 8)+'px';
        btn.style.display = 'block';
    });
    btn.addEventListener('click',()=>{
        if(!sel) return;
        const u = new URL(window.location.href);
        u.searchParams.set('ask_sel', sel);
        window.location.href = u.toString();
    });
})();
</script>
""", unsafe_allow_html=True)

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
    "storage_loaded": False,
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
    if final_expr and "$" not in final_expr:
        final_expr = f"${final_expr}$"
    pretty = (
        '<div class="final-answer"><strong>✅ คำตอบสุดท้าย</strong><br>'
        f'{final_expr}</div>'
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


def is_socratic_done(text: str, force_done: bool = False) -> bool:
    if force_done:
        return True
    raw = str(text)
    if re.search(r'\[\[STEP_STATUS:DONE\]\]', raw, flags=re.IGNORECASE):
        return True
    lowered = raw.lower()
    done_markers = ["คำตอบสุดท้าย", "final answer", "สรุปคำตอบสุดท้าย", "เฉลยครบ"]
    return any(marker in lowered for marker in done_markers)


def build_profile_prompt(level, speed, lang, mode) -> str:
    return (
        f"ผู้เรียน: ระดับ {level} | ความเร็ว: {speed} | ภาษา: {lang} | โหมด: {mode}\n"
        "ปรับเนื้อหาให้เหมาะกับระดับผู้เรียน และปรับความยาวคำอธิบายตามความเร็วที่เลือก"
    )


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
    try:
        payload = {
            "chat_history": st.session_state.chat_history,
            "current_chat": {
                "messages": sanitize_messages_for_storage(st.session_state.messages),
                "weakness_counts": st.session_state.weakness_counts,
                "quick_mode": st.session_state.quick_mode,
                "last_quick_mode": st.session_state.last_quick_mode,
            },
            "updated_at": now_iso(),
            "version": 1,
        }
        STORE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def load_store_once():
    if st.session_state.storage_loaded:
        return
    st.session_state.storage_loaded = True

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

        if isinstance(messages, list):
            st.session_state.messages = messages
        if isinstance(weakness, dict):
            st.session_state.weakness_counts = weakness
        if quick_mode in ["ติวละเอียด", "ฝึกทีละขั้น", "เฉลยไว"]:
            st.session_state.quick_mode = quick_mode
        if last_mode in ["ติวละเอียด", "ฝึกทีละขั้น", "เฉลยไว"]:
            st.session_state.last_quick_mode = last_mode


def reset_current_chat():
    st.session_state.messages = []
    st.session_state.pending_prompt = ""
    st.session_state.weakness_counts = {}
    st.session_state.socratic_continue = False
    st.session_state.socratic_can_continue = False
    save_store()


def archive_current_chat(mode_name: str):
    if not st.session_state.messages:
        return

    first_user = next(
        (m.get("content", "") for m in st.session_state.messages if m.get("role") == "user"),
        "แชทคณิตศาสตร์"
    )
    title = clean_snippet(first_user, 50) or "แชทคณิตศาสตร์"

    snapshot = {
        "id": f"chat_{int(time.time() * 1000)}",
        "title": title,
        "mode": mode_name,
        "messages": sanitize_messages_for_storage(st.session_state.messages),
        "weakness_counts": copy.deepcopy(st.session_state.weakness_counts),
        "updated_at": now_pretty(),
        "created_at": now_pretty(),
        "message_count": len(st.session_state.messages),
    }

    st.session_state.chat_history.insert(0, snapshot)
    st.session_state.chat_history = st.session_state.chat_history[:30]
    save_store()


def load_chat_snapshot(snapshot: dict):
    st.session_state.messages = copy.deepcopy(snapshot.get("messages", []))
    st.session_state.weakness_counts = copy.deepcopy(snapshot.get("weakness_counts", {}))
    st.session_state.pending_prompt = ""
    st.session_state.socratic_continue = False
    st.session_state.socratic_can_continue = False
    mode_from_snapshot = snapshot.get("mode", "ติวละเอียด")
    if mode_from_snapshot in ["ติวละเอียด", "ฝึกทีละขั้น", "เฉลยไว"]:
        st.session_state.quick_mode = mode_from_snapshot
        st.session_state.last_quick_mode = mode_from_snapshot
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

    model_short = MODEL_NAME.split("/")[-1].split("-distill")[0]
    st.markdown(
        f'<div class="header-meta" style="margin:4px 0 8px;">'
        f'<span class="status-dot"></span>'
        f'<span class="model-chip">✦ {model_short}</span></div>',
        unsafe_allow_html=True,
    )

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
                    st.session_state.chat_history = [
                        c for c in st.session_state.chat_history if c.get("id") != snap.get("id")
                    ]
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
            "\n8. ตอนท้ายให้ปิดด้วยประโยค: 'พร้อมแล้วกดปุ่ม ➡️ ไปต่อ'"
        )
        continue_step_instruction = (
            "\n7. เมื่อได้รับคำสั่ง 'ไปต่อ' ให้สอนเฉพาะขั้นถัดไป 1 ขั้นเท่านั้น"
            " และจบด้วยประโยค: 'พร้อมแล้วกดปุ่ม ➡️ ไปต่อ'"
            "\n8. ถ้ายังไม่จบข้อ ให้ใส่ [[STEP_STATUS:CONTINUE]] ต่อท้ายคำตอบ"
            "\n9. ถ้าจบข้อแล้วหรือให้คำตอบสุดท้าย ให้ใส่ [[STEP_STATUS:DONE]] ต่อท้ายคำตอบ"
        )

        stage_rule = continue_step_instruction if (is_continue_request or st.session_state.socratic_continue) else overview_only_instruction

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

    profile   = build_profile_prompt(learner_level, explain_speed, language_pref, tutor_mode)
    sys_prompt = f"{base_sys}\n\n{profile}"

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
                    content_text += "\n\n(ผู้ใช้แนบรูปมาแต่โมเดลนี้ไม่รองรับการดูรูป)"

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
            code_m   = re.search(r'```python\n(.*?)```', full_response, re.DOTALL)
            if code_m:
                try:
                    fig, ax = plt.subplots(facecolor='none')
                    ax.set_facecolor('#0d1117')
                    for spine in ax.spines.values():
                        spine.set_color('#334155')
                    ax.tick_params(colors='#94a3b8')
                    exec(
                        f"import numpy as np\n{code_m.group(1)}",
                        {"plt": plt, "np": np, "ax": ax},
                        {},
                    )
                    st.pyplot(fig)
                    plot_fig = fig
                except:
                    pass

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
            st.session_state.messages.append(res_msg)
            save_store()

        except Exception as e:
            st.error(f"🚨 เกิดข้อผิดพลาด: {e}")
            st.info("💡 ตรวจสอบ API Key หรือชื่อโมเดลครับ")