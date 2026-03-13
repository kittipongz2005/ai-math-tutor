import streamlit as st

GLOBAL_CSS = """
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
    margin: 0.7rem 0 0.7rem 1.2rem;
    overflow-x: auto;
    text-align: left !important;
}
.katex-display > .katex {
    text-align: left !important;
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
"""

KATEX_BLOCK = """
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
"""

SELECTION_ASK_BLOCK = """
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
"""


def apply_ui_decorations() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    st.markdown(KATEX_BLOCK, unsafe_allow_html=True)
    st.markdown(SELECTION_ASK_BLOCK, unsafe_allow_html=True)
