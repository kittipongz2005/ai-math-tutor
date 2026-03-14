from datetime import datetime

import streamlit as st

from worksheet_tools import (
    build_effective_weakness_counts,
    build_weakness_worksheet_html,
    build_weakness_worksheet_payload,
)


def render_worksheet_generator_ui(
    api_key: str,
    model_name: str,
    learner_level: str,
    language_pref: str,
) -> None:
    st.markdown("### 🖨️ Smart Worksheet Generator")
    st.text_area(
        "พิมพ์หัวข้อที่อ่อนเอง (คั่นด้วย , หรือขึ้นบรรทัดใหม่)",
        key="manual_weakness_text",
        height=76,
        placeholder="เช่น แคลคูลัส, ตรีโกณมิติ, เมทริกซ์",
    )

    effective_weakness_counts = build_effective_weakness_counts(
        st.session_state.weakness_counts,
        st.session_state.manual_weakness_text,
    )

    if not effective_weakness_counts:
        st.caption("ยังไม่มีข้อมูลจุดอ่อน ให้พิมพ์หัวข้อที่อ่อนเองด้านบน หรือถามโจทย์ก่อนอย่างน้อย 1 ครั้ง")
    else:
        top_preview = sorted(effective_weakness_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        st.caption("หัวข้อที่จะใช้สร้างใบงาน: " + ", ".join([f"{topic}" for topic, _ in top_preview]))

    worksheet_q_count = st.slider(
        "จำนวนข้อสำหรับใบงานทบทวน",
        min_value=5,
        max_value=10,
        value=7,
        step=1,
        key="worksheet_q_count",
    )

    if st.button("สร้างแบบฝึกหัดทบทวนจุดอ่อน", use_container_width=True, key="gen_weakness_worksheet"):
        if not api_key.strip():
            st.warning("กรุณาใส่ Groq API Key ก่อนสร้างใบงาน")
        else:
            with st.spinner("กำลังสร้างใบงานจากหัวข้อที่พลาดบ่อย..."):
                worksheet_payload, ws_err = build_weakness_worksheet_payload(
                    api_key=api_key.strip(),
                    model_name=model_name,
                    weakness_counts=effective_weakness_counts,
                    learner_level=learner_level,
                    language_pref=language_pref,
                    question_count=worksheet_q_count,
                )
                if ws_err:
                    st.error(ws_err)
                    st.session_state.worksheet_export_content = ""
                    st.session_state.worksheet_export_name = ""
                    st.session_state.worksheet_export_ready = False
                else:
                    worksheet_html = build_weakness_worksheet_html(
                        worksheet=worksheet_payload,
                        weakness_counts=effective_weakness_counts,
                    )
                    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.session_state.worksheet_export_content = worksheet_html
                    st.session_state.worksheet_export_name = f"weakness_worksheet_{stamp}.html"
                    st.session_state.worksheet_export_ready = True
                    st.success("สร้างใบงานสำเร็จ — ดาวน์โหลด HTML แล้วเปิดในเบราว์เซอร์เพื่อ Save as PDF")

    if st.session_state.worksheet_export_ready and st.session_state.worksheet_export_content:
        st.download_button(
            "ดาวน์โหลดใบงาน HTML (Save as PDF)",
            data=st.session_state.worksheet_export_content,
            file_name=st.session_state.worksheet_export_name or "weakness_worksheet.html",
            mime="text/html",
            use_container_width=True,
            key="download_weakness_worksheet_html",
        )
        st.caption("วิธีใช้งาน: เปิดไฟล์ HTML ใน Chrome/Edge → กด Ctrl+P → Save as PDF")
