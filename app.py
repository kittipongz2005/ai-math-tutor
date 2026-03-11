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
# 1. ตั้งค่าหน้าเว็บ
# -----------------------------------------
st.set_page_config(page_title="Math AI Cloud Ultimate", page_icon="🚀", layout="wide")
st.title("🚀 ติวเตอร์คณิตศาสตร์ AI (Cloud Edition)")

# -----------------------------------------
# 2. จัดการ State & ฟังก์ชันช่วยเหลือ
# -----------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

def fix_latex(text):
    t = text.replace(r'\[', '$$').replace(r'\]', '$$').replace(r'\(', '$').replace(r'\)', '$')
    translate_dict = {
        'Wykładnik': 'เลขชี้กำลัง', 'wykładnik': 'เลขชี้กำลัง',
        'tích phân': 'อินทิเกรต', 'Тогда': 'ดังนั้น', 'тогда': 'ดังนั้น',
        'Подставляем обратно': 'แทนค่ากลับลงไป', 'Ответ': 'คำตอบสุดท้าย:',
        'Получаем': 'จะได้ว่า', 'Следовательно': 'สรุปได้ว่า',
        'Имеем': 'เราจะได้', 'Где': 'โดยที่',
        'Интегрирование по частям': 'Integration by Parts', 'formula': 'สูตร', 'Formula': 'สูตร'
    }
    for foreign, th in translate_dict.items():
        t = t.replace(foreign, th)
    return t

# ฟังก์ชันแปลงรูปภาพเป็น Base64 เพื่อส่งขึ้น Cloud
def encode_image(img):
    buffered = io.BytesIO()
    img = img.convert('RGB') # ป้องกัน error จากไฟล์ PNG โปร่งใส
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# -----------------------------------------
# 3. แถบเครื่องมือด้านข้าง (Sidebar)
# -----------------------------------------
with st.sidebar:
    st.header("☁️ ตั้งค่าระบบ Cloud")
    
    # ช่องใส่ API Key 
    API_KEY = st.text_input("🔑 ใส่ Groq API Key:", type="password", help="รับฟรีที่ console.groq.com")
    
    # เลือกโมเดล
    MODEL_NAME = st.selectbox(
        "ชื่อโมเดล (Groq):", 
        ["llama-3.3-70b-versatile", "deepseek-r1-distill-llama-70b", "llama-3.2-90b-vision-preview"]
    )
    st.caption("💡 แนะนำ: ถ้าแนบรูปภาพด้วย ให้เลือกโมเดลลงท้ายด้วย vision-preview")

    response_style = st.selectbox(
        "รูปแบบการตอบของ AI:",
        ["📝 สอนและอธิบายละเอียด", "⚡️ เฉลยอย่างเดียว (กระชับ)"],
        disabled=st.session_state.processing
    )

    st.divider()

    st.header("📤 อัปโหลดเอกสาร/รูปภาพ")
    uploaded_file = st.file_uploader("แนบไฟล์ PDF, TXT หรือรูปโจทย์", type=["pdf", "txt", "png", "jpg", "jpeg"], disabled=st.session_state.processing)

    file_content = ""
    uploaded_img = None
    base64_image = None

    if uploaded_file:
        if uploaded_file.type.startswith("image/"):
            uploaded_img = Image.open(uploaded_file)
            base64_image = encode_image(uploaded_img)
            st.image(uploaded_img, caption="รูปภาพที่อัปโหลด", use_container_width=True)
        elif uploaded_file.type == "application/pdf":
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                file_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
                st.success("✅ อ่าน PDF สำเร็จ")
            except: st.error("อ่าน PDF ไม่ได้")
        else:
            file_content = uploaded_file.getvalue().decode("utf-8")
            st.success("✅ อ่านไฟล์สำเร็จ")

    st.divider()

    if st.button("🗑️ ล้างแชท", use_container_width=True, disabled=st.session_state.processing):
        st.session_state.messages = []
        st.rerun()

# -----------------------------------------
# 4. แสดงประวัติแชท
# -----------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image_show" in message:
            st.image(message["image_show"], width=300)

        content = message["content"]
        # แสดงผลถ้ามี <think>
        if message["role"] == "assistant" and "</think>" in str(content):
            parts = str(content).split("</think>")
            with st.expander("💡 ดูเบื้องหลังการคิด"):
                st.write(parts[0].replace("<think>", "").strip())
            st.markdown(fix_latex(parts[1].strip()))
        else:
            if isinstance(content, list): # กรณีส่งเป็นลิสต์ข้อความ+รูป
                st.markdown(fix_latex(content[0]["text"]))
            else:
                display_text = str(content).split("[ข้อมูลอ้างอิงจากไฟล์]")[0]
                st.markdown(fix_latex(display_text))

        if "plot" in message:
            st.pyplot(message["plot"])

# -----------------------------------------
# 5. รับข้อความ & จัดการคิว
# -----------------------------------------
prompt = st.chat_input("พิมพ์โจทย์ หรือสั่งให้ AI วิเคราะห์ไฟล์...", disabled=st.session_state.processing)

if prompt:
    if not API_KEY:
        st.error("⚠️ กรุณาใส่ Groq API Key ที่แถบด้านซ้ายก่อนครับ! (ไปเอาได้ฟรีที่ console.groq.com)")
        st.stop()

    # สร้าง Message แบบ Cloud (รองรับ Vision)
    if base64_image and "vision" in MODEL_NAME.lower():
        user_content = [
            {"type": "text", "text": prompt + ("\n[ข้อมูลอ้างอิงจากไฟล์]:\n" + file_content if file_content else "")},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
        user_msg = {"role": "user", "content": user_content, "image_show": uploaded_img}
    else:
        text_payload = prompt
        if file_content: text_payload += f"\n\n[ข้อมูลอ้างอิงจากไฟล์]:\n{file_content}"
        user_msg = {"role": "user", "content": text_payload}
        if uploaded_img: user_msg["image_show"] = uploaded_img

    st.session_state.messages.append(user_msg)
    st.session_state.processing = True
    st.rerun()

# -----------------------------------------
# 6. ระบบ AI ประมวลผลบน Cloud
# -----------------------------------------
if st.session_state.processing:
    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=API_KEY)
            
            instr = "อธิบายละเอียดใจดีและแสดงวิธีทำทีละขั้น" if "อธิบายละเอียด" in response_style else "เฉลยอย่างกระชับ"
            sys_prompt = f"""คุณคือติวเตอร์คณิตศาสตร์อัจฉริยะ ({instr}) 
            กฎเหล็ก:
            1. ตอบเฉพาะ 'สิ่งที่ผู้ใช้ถาม' เท่านั้น ห้ามทำข้ออื่นเด็ดขาด
            2. ใช้ภาษาไทย 100% (ศัพท์เทคนิคใช้ภาษาอังกฤษได้)
            3. ใช้ LaTeX ($ และ $$) เสมอ โดยครอบสมการทุกครั้ง
            4. หากต้องวาดกราฟ ให้เขียนโค้ด Python (matplotlib) ในบล็อก ```python"""

            # เตรียมข้อความส่งขึ้น Cloud
            messages_for_ai = [{'role': 'system', 'content': sys_prompt}]
            for m in st.session_state.messages:
                messages_for_ai.append({'role': m['role'], 'content': m['content']})

            full_response = ""
            is_thinking = False
            answer_placeholder = st.empty()

            start_time = time.time()

            # เรียก API
            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages_for_ai,
                stream=True
            )

            for chunk in stream:
                txt = chunk.choices[0].delta.content or ""
                full_response += txt

                if "<think>" in full_response and "</think>" not in full_response:
                    if not is_thinking:
                        is_thinking = True
                        status_container = st.status("🧠 AI กำลังคำนวณบนคลาวด์...", expanded=True)
                        think_text_placeholder = status_container.empty()
                    think_text_placeholder.markdown(full_response.split("<think>")[-1] + " ▌")
                elif "</think>" in full_response:
                    if is_thinking:
                        is_thinking = False
                        status_container.update(label="💡 คิดเสร็จแล้ว", state="complete", expanded=False)
                    answer_placeholder.markdown(fix_latex(full_response.split("</think>")[-1]) + " ▌")
                else:
                    answer_placeholder.markdown(fix_latex(full_response) + " ▌")

            final_answer = full_response.split("</think>")[-1] if "</think>" in full_response else full_response
            answer_placeholder.markdown(fix_latex(final_answer).strip())

            # วาดกราฟ
            plot_fig = None
            code_match = re.search(r'```python\n(.*?)```', full_response, re.DOTALL)
            if code_match:
                try:
                    code = code_match.group(1)
                    fig, ax = plt.subplots()
                    exec(f"import numpy as np\n{code}", {"plt": plt, "np": np, "ax": ax}, {})
                    st.pyplot(fig)
                    plot_fig = fig
                except: pass

            st.caption(f"⚡️ ความเร็วคลาวด์: {time.time() - start_time:.2f} วินาที")

            res_msg = {"role": "assistant", "content": full_response}
            if plot_fig: res_msg["plot"] = plot_fig
            st.session_state.messages.append(res_msg)

        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดจาก Cloud: {e} \n(ถ้าส่งรูปภาพ อย่าลืมเลือกโมเดลที่ลงท้ายด้วย vision)")
        finally:
            st.session_state.processing = False
            st.rerun()