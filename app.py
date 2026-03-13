import streamlit as st
import PyPDF2
import time
import io
import re
import base64
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
from groq import Groq

# -----------------------------------------
# ตั้งค่าหน้าเว็บ
# -----------------------------------------
st.set_page_config(
    page_title="Math AI Tutor",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------
# Custom CSS - Dark Mode + Glassmorphism
# -----------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Noto+Sans+Thai:wght@300;400;500;600;700&display=swap');

/* === GLOBAL RESET === */
*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Inter', 'Noto Sans Thai', sans-serif;
}

/* === DARK BACKGROUND === */
.stApp {
    background: linear-gradient(135deg, #0d0d1a 0%, #0a1628 40%, #0d1f2d 100%);
    min-height: 100vh;
}

/* === MAIN CONTENT AREA === */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2rem !important;
    max-width: 900px !important;
}

/* === TITLE === */
h1 {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 50%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 700 !important;
    font-size: 2rem !important;
    letter-spacing: -0.5px;
    margin-bottom: 0.25rem !important;
}

/* === SIDEBAR === */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1923 0%, #111827 100%) !important;
    border-right: 1px solid rgba(79, 172, 254, 0.15) !important;
}

[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

/* Sidebar Headers */
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
    color: #4facfe !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.75rem !important;
}

/* === INPUT FIELDS === */
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] select {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(79,172,254,0.25) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-family: 'Inter', 'Noto Sans Thai', sans-serif !important;
}

[data-testid="stTextInput"] input:focus {
    border-color: rgba(79,172,254,0.7) !important;
    box-shadow: 0 0 0 3px rgba(79,172,254,0.12) !important;
}

/* === BUTTONS === */
.stButton button {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%) !important;
    color: #0d0d1a !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Inter', 'Noto Sans Thai', sans-serif !important;
    transition: all 0.2s ease !important;
    padding: 0.5rem 1rem !important;
}

.stButton button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(79,172,254,0.35) !important;
}

/* === FILE UPLOADER === */
[data-testid="stFileUploader"] {
    background: rgba(79,172,254,0.04) !important;
    border: 1.5px dashed rgba(79,172,254,0.3) !important;
    border-radius: 12px !important;
    padding: 0.75rem !important;
    transition: border-color 0.2s ease !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(79,172,254,0.6) !important;
}

/* === CHAT MESSAGES === */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 16px !important;
    padding: 1rem 1.25rem !important;
    margin-bottom: 0.75rem !important;
    backdrop-filter: blur(10px) !important;
}

/* User message */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: rgba(79,172,254,0.08) !important;
    border-color: rgba(79,172,254,0.15) !important;
}

/* AI message */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background: rgba(167,139,250,0.06) !important;
    border-color: rgba(167,139,250,0.12) !important;
}

/* === CHAT INPUT === */
[data-testid="stChatInput"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1.5px solid rgba(79,172,254,0.3) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(10px) !important;
}

[data-testid="stChatInput"]:focus-within {
    border-color: rgba(79,172,254,0.7) !important;
    box-shadow: 0 0 0 3px rgba(79,172,254,0.1) !important;
}

[data-testid="stChatInput"] textarea {
    color: #e2e8f0 !important;
    font-family: 'Inter', 'Noto Sans Thai', sans-serif !important;
}

/* === TEXT COLORS === */
p, li, span, label { color: #cbd5e1 !important; }
strong { color: #e2e8f0 !important; }
code { color: #4facfe !important; background: rgba(79,172,254,0.1) !important; border-radius: 4px !important; padding: 1px 5px !important; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    line-height: 1.75 !important;
}

.katex-display {
    background: rgba(79, 172, 254, 0.06);
    border: 1px solid rgba(79, 172, 254, 0.22);
    border-radius: 10px;
    padding: 10px 12px;
    margin: 0.65rem 0;
    overflow-x: auto;
}

.final-answer {
    background: rgba(34, 197, 94, 0.08);
    border: 1px solid rgba(34, 197, 94, 0.25);
    border-radius: 12px;
    padding: 10px 12px;
    margin-top: 0.75rem;
}

#selection-ask-btn {
    position: fixed;
    z-index: 9999;
    display: none;
    border: none;
    border-radius: 999px;
    padding: 8px 12px;
    font-weight: 700;
    font-size: 0.82rem;
    color: #0d0d1a;
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    box-shadow: 0 10px 24px rgba(0, 242, 254, 0.35);
    cursor: pointer;
}

#selection-ask-btn:hover {
    transform: translateY(-1px);
}

/* === EXPANDER (Thinking box) === */
[data-testid="stExpander"] {
    background: rgba(251,191,36,0.05) !important;
    border: 1px solid rgba(251,191,36,0.2) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

[data-testid="stExpander"] summary {
    color: #fbbf24 !important;
    font-weight: 600 !important;
}

/* === STATUS CONTAINER === */
[data-testid="stStatus"] {
    background: rgba(79,172,254,0.06) !important;
    border: 1px solid rgba(79,172,254,0.2) !important;
    border-radius: 12px !important;
}

/* === DIVIDER === */
hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 1rem 0 !important;
}

/* === SUCCESS / ERROR / INFO === */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left-width: 3px !important;
}

/* === CAPTION === */
.stCaption { color: #64748b !important; font-size: 0.75rem !important; }

/* === SCROLLBAR === */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(79,172,254,0.3); border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: rgba(79,172,254,0.6); }

/* === IMAGE IN CHAT === */
img { border-radius: 10px !important; }

/* === SUBHEADER BADGE === */
.model-badge {
    display: inline-block;
    background: linear-gradient(135deg, #4facfe22, #a78bfa22);
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.75rem;
    color: #a78bfa;
    font-weight: 500;
    margin-left: 8px;
    vertical-align: middle;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<script>
(function() {
    if (window.__selectionAskInit__) return;
    window.__selectionAskInit__ = true;

    const btn = document.createElement('button');
    btn.id = 'selection-ask-btn';
    btn.innerText = 'ถามข้อความที่คลุม';
    document.body.appendChild(btn);

    let selectedText = '';

    const hideBtn = () => {
        btn.style.display = 'none';
    };

    document.addEventListener('mousedown', () => {
        hideBtn();
    });

    document.addEventListener('mouseup', (event) => {
        const sel = window.getSelection ? window.getSelection().toString().trim() : '';
        if (!sel || sel.length < 2) {
            hideBtn();
            return;
        }

        selectedText = sel.slice(0, 500);
        btn.style.left = `${Math.min(event.clientX + 8, window.innerWidth - 180)}px`;
        btn.style.top = `${Math.max(event.clientY - 42, 8)}px`;
        btn.style.display = 'block';
    });

    btn.addEventListener('click', () => {
        if (!selectedText) return;
        const url = new URL(window.location.href);
        url.searchParams.set('ask_selection', selectedText);
        window.location.href = url.toString();
    });
})();
</script>
""", unsafe_allow_html=True)

# inject KaTeX for math rendering
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {
        delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false}
        ],
        throwOnError: false
    });"></script>
""", unsafe_allow_html=True)

# -----------------------------------------
# Header
# -----------------------------------------
col_title, col_badge = st.columns([3, 1])
with col_title:
    st.title("🧮 Math AI Tutor")
    st.caption("ติวเตอร์คณิตศาสตร์ AI — อธิบายละเอียด ทุกขั้นตอน")

# -----------------------------------------
# State & Helper Functions
# -----------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = ""

if "weakness_counts" not in st.session_state:
    st.session_state.weakness_counts = {}

def fix_latex(text):
    t = str(text)
    t = t.replace(r'\[', '$$').replace(r'\]', '$$')
    t = t.replace(r'\(', '$').replace(r'\)', '$')
    translate_dict = {
        'Wykładnik': 'เลขชี้กำลัง', 'wykładnik': 'เลขชี้กำลัง',
        'tích phân': 'อินทิเกรต', 'Тогда': 'ดังนั้น', 'тогда': 'ดังนั้น',
        'Подставляем обратно': 'แทนค่ากลับลงไป', 'Ответ': 'คำตอบสุดท้าย:',
        'Получаем': 'จะได้ว่า', 'Следовательно': 'สรุปได้ว่า',
        'Имеем': 'เราจะได้', 'Где': 'โดยที่',
        'Интегрирование по частям': 'Integration by Parts',
        'formula': 'สูตร', 'Formula': 'สูตร'
    }
    for foreign, th in translate_dict.items():
        t = t.replace(foreign, th)
    return t

def ensure_math_renderable(text):
    t = str(text).strip()
    if not t:
        return t

    if t.lstrip().startswith("&") and "\\end{aligned}" in t and "\\begin{aligned}" not in t:
        t = "\\begin{aligned}\n" + t

    if "\\begin{aligned}" in t and "\\end{aligned}" not in t:
        t = t + "\n\\end{aligned}"

    has_aligned = "\\begin{aligned}" in t and "\\end{aligned}" in t
    if has_aligned and "$$" not in t:
        t = f"$$\n{t}\n$$"

    has_latex_commands = bool(re.search(r'\\(frac|int|sum|sqrt|cdot|times|left|right|text)', t))
    if t.lstrip().startswith("&") and "$" not in t:
        t = f"$$\n\\begin{{aligned}}\n{t}\n\\end{{aligned}}\n$$"
    elif has_latex_commands and "$" not in t and "\\n" in t:
        t = f"$$\n{t}\n$$"

    return t

def beautify_answer_text(text):
    t = fix_latex(text)
    t = ensure_math_renderable(t)

    final_pattern = re.compile(r'(\*\*คำตอบสุดท้าย:?\*\*|คำตอบสุดท้าย:)\s*(.+)', re.DOTALL)
    m = final_pattern.search(t)
    if not m:
        return t

    body = t[:m.start()].strip()
    final_expr = m.group(2).strip()
    if final_expr and "$" not in final_expr:
        final_expr = f"${final_expr}$"

    pretty_final = (
        '<div class="final-answer"><strong>✅ คำตอบสุดท้าย</strong><br>'
        f'{final_expr}'
        '</div>'
    )

    return (body + "\n\n" if body else "") + pretty_final

def encode_image(img):
    buffered = io.BytesIO()
    img = img.convert('RGB')
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def count_tokens_approx(text):
    """ประมาณจำนวน Token (หยาบๆ) จากจำนวนอักขระ"""
    return max(1, len(str(text)) // 4)

def split_text_chunks(text, chunk_size=700):
    text = (text or "").strip()
    if not text:
        return []
    normalized = re.sub(r'\n{3,}', '\n\n', text)
    paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
    chunks = []
    current = ""
    for para in paragraphs:
        candidate = f"{current}\n\n{para}".strip() if current else para
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(para) <= chunk_size:
                current = para
            else:
                for i in range(0, len(para), chunk_size):
                    chunks.append(para[i:i + chunk_size])
                current = ""
    if current:
        chunks.append(current)
    return chunks

def extract_topics(text):
    topic_keywords = {
        "พีชคณิต": ["สมการ", "แยกตัวประกอบ", "กำลัง", "log", "พหุนาม", "algebra"],
        "แคลคูลัส": ["อนุพันธ์", "อินทิเกรต", "ลิมิต", "ปริพันธ์", "derivative", "integral", "limit"],
        "ตรีโกณมิติ": ["sin", "cos", "tan", "ตรีโกณ", "เรเดียน", "มุม"],
        "เรขาคณิต": ["พื้นที่", "ปริมาตร", "วงกลม", "สามเหลี่ยม", "เรขาคณิต", "geometry"],
        "สถิติ": ["ความน่าจะเป็น", "ค่าเฉลี่ย", "ส่วนเบี่ยงเบน", "variance", "probability", "statistics"],
        "เมทริกซ์": ["เมทริกซ์", "det", "determinant", "eigen", "เวกเตอร์", "vector"]
    }
    lower = str(text).lower()
    found = []
    for topic, keywords in topic_keywords.items():
        if any(k.lower() in lower for k in keywords):
            found.append(topic)
    return found

def update_weakness_profile(text):
    for topic in extract_topics(text):
        st.session_state.weakness_counts[topic] = st.session_state.weakness_counts.get(topic, 0) + 1

def build_profile_prompt(level, explain_speed, language_pref, tutor_mode):
    return f"""
ข้อมูลผู้เรียน:
- ระดับผู้เรียน: {level}
- ความเร็วการสอน: {explain_speed}
- ภาษาที่ใช้ตอบ: {language_pref}
- โหมดการติว: {tutor_mode}

ข้อกำหนดเพิ่มเติม:
1. ปรับระดับเนื้อหาให้เหมาะกับระดับผู้เรียน
2. ถ้าผู้เรียนบอกว่าติดตรงไหน ให้โฟกัสแก้จุดนั้นก่อน
3. ใช้คำอธิบายสั้น/ยาวตามความเร็วการสอนที่เลือก
""".strip()

def clean_snippet(text, max_len=180):
    one_line = re.sub(r'\s+', ' ', str(text)).strip()
    return (one_line[:max_len] + "...") if len(one_line) > max_len else one_line

selected_from_query = st.query_params.get("ask_selection", "")
if isinstance(selected_from_query, list):
    selected_from_query = selected_from_query[0] if selected_from_query else ""

selected_from_query = str(selected_from_query).strip()
if selected_from_query:
    st.session_state.pending_prompt = (
        f"ฉันคลุมข้อความนี้จากคำตอบ AI:\n\"{selected_from_query}\"\n\n"
        "ช่วยอธิบายส่วนนี้แบบเข้าใจง่าย พร้อมบอกสูตรที่เกี่ยวข้องและยกตัวอย่างสั้น ๆ"
    )
    if "ask_selection" in st.query_params:
        del st.query_params["ask_selection"]
    st.rerun()

# -----------------------------------------
# Sidebar
# -----------------------------------------
with st.sidebar:
    st.markdown("## ☁️ ตั้งค่าระบบ")

    API_KEY = st.text_input(
        "🔑 Groq API Key",
        type="password",
        placeholder="gsk_...",
        help="รับฟรีที่ console.groq.com"
    )

    quick_mode = st.radio(
        "🚀 โหมดใช้งานเร็ว",
        ["ติวละเอียด", "ฝึกทีละขั้น", "เฉลยไว"],
        horizontal=True,
        help="เลือกแบบเร็ว ๆ ได้เลย ถ้าต้องการปรับเองค่อยเปิดตั้งค่าเพิ่มเติม"
    )

    model_options = [
        "qwen/qwen3-32b",
        "deepseek-r1-distill-llama-70b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
    ]

    MODEL_NAME = "qwen/qwen3-32b"
    if quick_mode == "ฝึกทีละขั้น":
        response_style = "📝 สอนและอธิบายละเอียด"
        tutor_mode = "โหมดฝึกทีละขั้น (Socratic)"
    elif quick_mode == "เฉลยไว":
        response_style = "⚡️ เฉลยอย่างเดียว"
        tutor_mode = "โหมดปกติ"
    else:
        response_style = "📝 สอนและอธิบายละเอียด"
        tutor_mode = "โหมดปกติ"

    learner_level = "ม.ปลาย"
    explain_speed = "พอดี"
    language_pref = "ไทย"

    with st.expander("⚙️ ตั้งค่าเพิ่มเติม (ไม่จำเป็น)", expanded=False):
        MODEL_NAME = st.selectbox(
            "🤖 เลือกโมเดล",
            model_options,
            index=0,
            help="ค่าเริ่มต้นเป็น qwen3-32b"
        )

        manual_override = st.checkbox("ปรับค่าการสอนเอง", value=False)
        if manual_override:
            response_style = st.selectbox(
                "📐 รูปแบบการตอบ",
                ["📝 สอนและอธิบายละเอียด", "⚡️ เฉลยอย่างเดียว"],
                key="style_memory"
            )

            tutor_mode = st.selectbox(
                "🎯 โหมดติวเตอร์",
                ["โหมดปกติ", "โหมดฝึกทีละขั้น (Socratic)"],
                help="โหมดฝึกจะไม่เฉลยรวดเดียว แต่จะพาคิดทีละขั้นเหมือนติวเตอร์ส่วนตัว"
            )

            learner_level = st.selectbox(
                "🧑‍🎓 ระดับผู้เรียน",
                ["ม.ต้น", "ม.ปลาย", "มหาวิทยาลัยปีต้น", "มหาวิทยาลัยปีสูง"]
            )

            explain_speed = st.selectbox(
                "⏱️ ความเร็วการอธิบาย",
                ["ช้าและละเอียด", "พอดี", "กระชับเร็ว"]
            )

            language_pref = st.selectbox(
                "🌐 ภาษาในการตอบ",
                ["ไทย", "ไทย+อังกฤษศัพท์สำคัญ", "English"]
            )

    model_short = MODEL_NAME.split("/")[-1].split("-distill")[0]
    st.caption(f"✨ โมเดล: {model_short}")

    st.divider()

    # --- Upload Section ---
    st.markdown("## 📎 แนบไฟล์")
    uploaded_file = st.file_uploader(
        "PDF, TXT หรือรูปโจทย์",
        type=["pdf", "txt", "png", "jpg", "jpeg"],
        label_visibility="collapsed"
    )

    file_content = ""
    uploaded_img = None
    base64_image = None

    if uploaded_file:
        ftype = uploaded_file.type
        if ftype.startswith("image/"):
            uploaded_img = Image.open(uploaded_file)
            base64_image = encode_image(uploaded_img)
            st.image(uploaded_img, caption="📸 รูปภาพที่อัปโหลด", use_container_width=True)
            st.success("✅ โหลดรูปสำเร็จ")

        elif ftype == "application/pdf":
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                pages = [page.extract_text() or "" for page in pdf_reader.pages]
                file_content = "\n".join(pages)
                n_pages = len(pdf_reader.pages)
                approx_tok = count_tokens_approx(file_content)
                st.success(f"✅ PDF {n_pages} หน้า (~{approx_tok:,} tokens)")
            except Exception as e:
                st.error(f"อ่าน PDF ไม่ได้: {e}")
        else:
            try:
                file_content = uploaded_file.getvalue().decode("utf-8")
                approx_tok = count_tokens_approx(file_content)
                st.success(f"✅ ไฟล์ข้อความ (~{approx_tok:,} tokens)")
            except:
                st.error("อ่านไฟล์ไม่ได้")

    st.divider()

    # --- Stats & Actions ---
    total_msgs = len(st.session_state.messages)
    total_chars = sum(len(str(m.get("content", ""))) for m in st.session_state.messages)

    with st.expander("📊 สถิติและคำแนะนำ", expanded=False):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("💬 ข้อความ", total_msgs)
        with col_s2:
            st.metric("📊 ~Tokens", f"{count_tokens_approx(total_chars * 4):,}")

        if st.session_state.weakness_counts:
            st.markdown("### 📌 จุดที่ควรทบทวน")
            top_topics = sorted(
                st.session_state.weakness_counts.items(),
                key=lambda item: item[1],
                reverse=True
            )[:3]
            topic_to_prompt = {
                "พีชคณิต": "ช่วยออกแบบแบบฝึกหัดพีชคณิต 3 ข้อ โดยไล่ง่ายไปยากและเฉลยทีละขั้น",
                "แคลคูลัส": "ช่วยทบทวนแคลคูลัสหัวข้ออนุพันธ์/อินทิเกรตแบบสั้น แล้วให้โจทย์ฝึก 2 ข้อ",
                "ตรีโกณมิติ": "ช่วยสรุปตรีโกณมิติที่มักสับสน พร้อมตัวอย่างโจทย์ 2 ข้อ",
                "เรขาคณิต": "ช่วยสรุปสูตรเรขาคณิตที่ต้องจำ และทดสอบฉันด้วยโจทย์ 2 ข้อ",
                "สถิติ": "ช่วยติวสถิติพื้นฐานแบบเข้าใจง่าย พร้อมโจทย์ฝึก 2 ข้อ",
                "เมทริกซ์": "ช่วยสอนเมทริกซ์ทีละขั้น และให้แบบฝึกหัดพร้อมตรวจคำตอบ"
            }
            for topic, cnt in top_topics:
                st.write(f"- {topic} ({cnt} ครั้ง)")
                if st.button(f"ฝึกเพิ่ม: {topic}", key=f"practice_{topic}", use_container_width=True):
                    st.session_state.pending_prompt = topic_to_prompt.get(topic, f"ช่วยสอนเรื่อง {topic} แบบติวเตอร์ส่วนตัว")
                    st.rerun()

    if st.button("🗑️ ล้างการสนทนา", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_prompt = ""
        st.session_state.weakness_counts = {}
        st.rerun()

    st.caption("🔒 API Key ของคุณไม่ถูกบันทึก")

# -----------------------------------------
# แสดงประวัติแชท
# -----------------------------------------
for msg_idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if "image_show" in message:
            st.image(message["image_show"], width=280)

        content = message["content"]

        if message["role"] == "assistant" and "</think>" in str(content):
            parts = str(content).split("</think>")
            think_text = parts[0].replace("<think>", "").strip()
            answer_text = parts[1].strip()

            with st.expander("💡 กระบวนการคิดของ AI", expanded=False):
                st.markdown(f'<div style="font-size:0.85rem; color:#94a3b8; line-height:1.7;">{think_text}</div>',
                            unsafe_allow_html=True)
            st.markdown(beautify_answer_text(answer_text), unsafe_allow_html=True)
        else:
            st.markdown(beautify_answer_text(str(content)), unsafe_allow_html=True)

        if message["role"] == "assistant":
            final_msg_text = str(content).split("</think>")[-1].strip()
            follow_up_prompts = [
                ("❓ ทำไมใช้สูตรนี้", "ช่วยอธิบายว่าทำไมถึงเลือกใช้สูตรในคำตอบนี้"),
                ("🧠 ขอช้าลง", "ช่วยอธิบายใหม่แบบช้าลงและละเอียดขึ้น โดยเน้นขั้นที่สับสน"),
                ("📝 ขอแบบฝึก", "ช่วยสร้างโจทย์คล้ายกัน 2 ข้อ และรอให้ฉันลองทำก่อนเฉลย"),
                ("🔍 เฉพาะจุดที่งง", "ช่วยโฟกัสเฉพาะจุดที่คนมักผิดในวิธีทำข้อนี้")
            ]
            if "Socratic" in tutor_mode:
                follow_up_prompts = [
                    ("➡️ ไปต่อ", "ไปต่อขั้นถัดไปจากจุดล่าสุด 1 ขั้น โดยยังไม่เฉลยทั้งหมด"),
                    ("❓ ทำไมใช้สูตรนี้", "ช่วยอธิบายว่าทำไมถึงเลือกใช้สูตรในคำตอบนี้"),
                    ("🧠 ขอช้าลง", "ช่วยอธิบายใหม่แบบช้าลงและละเอียดขึ้น โดยเน้นขั้นที่สับสน"),
                    ("📝 ขอแบบฝึก", "ช่วยสร้างโจทย์คล้ายกัน 2 ข้อ และรอให้ฉันลองทำก่อนเฉลย")
                ]
            cols = st.columns(4)
            for i, (label, q_text) in enumerate(follow_up_prompts):
                with cols[i]:
                    if st.button(label, key=f"followup_{msg_idx}_{i}", use_container_width=True):
                        if label == "➡️ ไปต่อ":
                            st.session_state.pending_prompt = f"จากคำตอบล่าสุดนี้: {clean_snippet(final_msg_text, 220)}\n\nไปต่อ"
                        else:
                            st.session_state.pending_prompt = f"จากคำตอบนี้: {clean_snippet(final_msg_text, 220)}\n\n{q_text}"
                        st.rerun()

        if "plot" in message:
            st.pyplot(message["plot"])

# -----------------------------------------
# Chat Input & AI Response
# -----------------------------------------
typed_prompt = st.chat_input("✏️  พิมพ์โจทย์คณิตศาสตร์ หรือถามสิ่งที่สงสัย...")
queued_prompt = st.session_state.pending_prompt.strip()
prompt = typed_prompt if typed_prompt else (queued_prompt if queued_prompt else "")

if prompt:

    if queued_prompt and not typed_prompt:
        st.session_state.pending_prompt = ""

    if not API_KEY.strip():
        st.error("⚠️ กรุณาใส่ Groq API Key ที่แถบด้านซ้ายก่อนครับ")
        st.stop()

    update_weakness_profile(prompt)

    # บันทึก + แสดงข้อความผู้ใช้
    user_msg = {"role": "user", "content": prompt}
    if uploaded_img:
        user_msg["image_show"] = uploaded_img
    st.session_state.messages.append(user_msg)

    with st.chat_message("user"):
        if uploaded_img:
            st.image(uploaded_img, width=280)
        st.markdown(prompt)

    # เรียก AI
    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=API_KEY.strip())

            is_deepseek = "deepseek" in MODEL_NAME.lower()
            is_vision = "vision" in MODEL_NAME.lower()

            # System Prompt
            if "Socratic" in tutor_mode:
                base_sys_prompt = """คุณคือติวเตอร์คณิตศาสตร์ส่วนตัว (โหมดฝึกทีละขั้น)
กฎเหล็ก:
1. ห้ามเฉลยรวดเดียวตั้งแต่ต้น
2. ให้ถามคำถามชี้นำทีละขั้น และเว้นจังหวะให้ผู้เรียนลองคิด
3. ให้ feedback สั้น กระชับ ชี้จุดผิดแบบเฉพาะจุด
4. ถ้าผู้เรียนพิมพ์ว่า 'เฉลยเต็ม' ค่อยแสดงวิธีทำครบทุกขั้น
5. ถ้าผู้เรียนพิมพ์ว่า 'ไปต่อ' ให้สอนขั้นถัดไปทันที 1 ขั้น โดยยังไม่เฉลยทั้งหมด
6. ทุกสมการต้องอยู่ในรูป LaTeX"""
            elif "อธิบายละเอียด" in response_style:
                base_sys_prompt = """คุณคืออาจารย์คณิตศาสตร์ระดับมหาวิทยาลัย (โหมดอธิบายละเอียด)
กฎเหล็ก:
1. อธิบายเหมือนสอนนักเรียนที่พื้นฐานอ่อน บอกเหตุผลเสมอว่า 'ทำไมถึงใช้สูตรนี้'
2. แบ่งโครงสร้างชัดเจน: **1. วิเคราะห์โจทย์** → **2. แสดงวิธีทำ** → **3. สรุปคำตอบ**
3. ใช้คำว่า อินทิเกรต หรือ หาปริพันธ์ (ไม่ใช่ 'ค่าอนันต์')
4. บังคับใช้ LaTeX ครอบสมการทุกครั้ง ($...$ สำหรับในบรรทัด, $$...$$ สำหรับแยกบรรทัด)
5. ตอบเฉพาะข้อที่ผู้ใช้สั่ง"""
            else:
                base_sys_prompt = """คุณคือเครื่องคิดเลขคณิตศาสตร์ (โหมดเฉลยอย่างเดียว)
กฎเหล็ก:
1. ห้ามเขียนคำบรรยายภาษาไทย ห้ามมีคำอธิบายทฤษฎีใดๆ (ยกเว้น 'คำตอบสุดท้าย:')
2. แสดงเฉพาะบรรทัดสมการเรียงลงมาจนจบ
3. ใช้ LaTeX แบบ Aligned: $$ \\begin{aligned} ... \\end{aligned} $$
4. บรรทัดล่างสุดพิมพ์ **คำตอบสุดท้าย:** ตามด้วยสมการ
5. ตอบเฉพาะข้อที่ผู้ใช้สั่ง"""

            socratic_rules = """
กฎสำหรับโหมดฝึกทีละขั้น (Socratic):
1. ห้ามเฉลยรวดเดียวตั้งแต่ต้น
2. ให้ถามคำถามชี้นำทีละขั้น แล้วรอผู้เรียนตอบ
3. ตรวจคำตอบผู้เรียนอย่างสุภาพและชี้จุดผิดแบบเฉพาะจุด
4. เฉลยเต็มรูปแบบได้เมื่อผู้เรียนพิมพ์ว่า 'เฉลยเต็ม' เท่านั้น
5. ถ้าผู้เรียนพิมพ์ว่า 'ไปต่อ' ให้เดินต่อเพียง 1 ขั้น แล้วถามกลับ
""" if "Socratic" in tutor_mode else ""

            profile_prompt = build_profile_prompt(learner_level, explain_speed, language_pref, tutor_mode)
            sys_prompt = f"{base_sys_prompt}\n\n{profile_prompt}\n\n{socratic_rules}".strip()

            messages_for_ai = []

            if not is_deepseek:
                messages_for_ai.append({'role': 'system', 'content': sys_prompt})

            for i, m in enumerate(st.session_state.messages):
                role = m['role']
                content_text = str(m['content'])

                if is_deepseek and i == 0 and role == 'user':
                    content_text = f"[คำสั่งระบบ: {sys_prompt}]\n\n" + content_text

                if i == len(st.session_state.messages) - 1 and role == 'user':
                    if file_content:
                        content_text += f"\n\n[ข้อมูลอ้างอิงจากไฟล์]:\n{file_content[:4000]}"

                    if base64_image:
                        if is_vision:
                            payload = [
                                {"type": "text", "text": content_text},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                            messages_for_ai.append({'role': role, 'content': payload})
                            continue
                        else:
                            content_text += "\n\n(ผู้ใช้แนบรูปมาด้วย แต่โมเดลนี้ไม่รองรับการดูรูปภาพ)"

                messages_for_ai.append({'role': role, 'content': content_text})

            # Streaming
            full_response = ""
            is_thinking = False
            answer_placeholder = st.empty()
            start_time = time.time()

            with st.spinner(""):
                stream = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages_for_ai,
                    stream=True
                )

            status_container = None

            for chunk in stream:
                txt = chunk.choices[0].delta.content or ""
                full_response += txt

                if "<think>" in full_response and "</think>" not in full_response:
                    if not is_thinking:
                        is_thinking = True
                        status_container = st.status("🧠 AI กำลังคิดวิเคราะห์...", expanded=True)
                        think_placeholder = status_container.empty()
                    think_text = full_response.split("<think>")[-1]
                    think_placeholder.markdown(
                        f'<div style="font-size:0.82rem; color:#94a3b8; line-height:1.8;">{think_text} ▌</div>',
                        unsafe_allow_html=True
                    )
                elif "</think>" in full_response:
                    if is_thinking:
                        is_thinking = False
                        if status_container:
                            status_container.update(label="✅ คิดเสร็จแล้ว", state="complete", expanded=False)
                    answer_placeholder.markdown(
                        beautify_answer_text(full_response.split("</think>")[-1]) + " ▌",
                        unsafe_allow_html=True
                    )
                else:
                    answer_placeholder.markdown(beautify_answer_text(full_response) + " ▌", unsafe_allow_html=True)

            # Final display
            final_answer = full_response.split("</think>")[-1] if "</think>" in full_response else full_response
            answer_placeholder.markdown(beautify_answer_text(final_answer).strip(), unsafe_allow_html=True)

            # Auto-plot graph
            plot_fig = None
            code_match = re.search(r'```python\n(.*?)```', full_response, re.DOTALL)
            if code_match:
                try:
                    code = code_match.group(1)
                    fig, ax = plt.subplots(facecolor='none')
                    ax.set_facecolor('#0d1117')
                    ax.tick_params(colors='#94a3b8')
                    ax.spines['bottom'].set_color('#334155')
                    ax.spines['left'].set_color('#334155')
                    ax.spines['top'].set_color('#334155')
                    ax.spines['right'].set_color('#334155')
                    exec(f"import numpy as np\n{code}", {"plt": plt, "np": np, "ax": ax}, {})
                    st.pyplot(fig)
                    plot_fig = fig
                except:
                    pass

            elapsed = time.time() - start_time
            st.caption(f"⚡️ ตอบใน {elapsed:.2f} วินาที  •  โมเดล: {model_short}")

            # บันทึก Response
            res_msg = {"role": "assistant", "content": full_response}
            if plot_fig:
                res_msg["plot"] = plot_fig
            st.session_state.messages.append(res_msg)

        except Exception as e:
            st.error(f"🚨 เกิดข้อผิดพลาด: {e}")
            st.info("💡 ลองตรวจสอบ API Key หรือชื่อโมเดลที่เลือกครับ")