import html
import re
from datetime import datetime


def build_chat_export_html(messages: list, clean_text_fn) -> str:
    blocks = []
    for idx, msg in enumerate(messages, 1):
        role = "ผู้ใช้" if msg.get("role") == "user" else "AI ติวเตอร์"
        role_class = "user" if msg.get("role") == "user" else "assistant"
        content = clean_text_fn(str(msg.get("content", ""))).strip() or "(ว่าง)"
        safe_content = html.escape(content)
        safe_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe_content)
        blocks.append(
            f'<article class="msg {role_class}">'
            f'<div class="meta">{idx}. {role}</div>'
            f'<div class="content math-zone">{safe_content}</div>'
            f'</article>'
        )

    exported_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!doctype html>
<html lang=\"th\">
<head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Math AI Tutor Chat Export</title>
    <link rel=\"preconnect\" href=\"https://cdn.jsdelivr.net\" />
    <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css\" />
    <style>
        :root {{ color-scheme: light; }}
        body {{
            margin: 0;
            padding: 24px;
            background: #f8fafc;
            color: #0f172a;
            font-family: "Noto Sans Thai", "Sarabun", "Segoe UI", Tahoma, Arial, sans-serif;
            line-height: 1.7;
        }}
        .wrap {{ max-width: 980px; margin: 0 auto; }}
        h1 {{ margin: 0 0 6px; font-size: 1.55rem; }}
        .sub {{ color: #475569; margin-bottom: 16px; }}
        .msg {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 12px 14px;
            margin: 10px 0;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
        }}
        .msg.user {{ border-left: 4px solid #3b82f6; }}
        .msg.assistant {{ border-left: 4px solid #8b5cf6; }}
        .meta {{ font-size: 0.86rem; color: #334155; font-weight: 700; margin-bottom: 6px; }}
        .content {{ white-space: pre-wrap; overflow-wrap: anywhere; }}
        .katex-display {{
            overflow-x: auto;
            overflow-y: hidden;
            padding: 2px 0;
            margin: 0.5rem 0 0.5rem 1.2rem;
            text-align: left !important;
        }}
        .katex-display > .katex {{ text-align: left !important; }}
    </style>
</head>
<body>
    <main class=\"wrap\">
        <h1>Math AI Tutor Chat Export</h1>
        <div class=\"sub\">Exported: {exported_at}</div>
        {''.join(blocks)}
    </main>

    <script defer src=\"https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js\"></script>
    <script defer src=\"https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js\"
        onload=\"renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}},{{left:'$',right:'$',display:false}}],throwOnError:false}});\"></script>
</body>
</html>
"""
