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

def fix_latex(text):
    t = str(text).replace(r'\[', '$$').replace(r'\]', '$$').replace(r'\(', '$').replace(r'\)', '$')
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

def encode_image(img):
    buffered = io.BytesIO()
    img = img.convert('RGB')
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# -----------------------------------------
# 3. แถบเครื่องมือด้านข้าง (Sidebar)
# -----------------------------------------
with st.sidebar:
    st.header("☁️ ตั้งค่าระบบ Cloud")
    
    API_KEY = st.text_input("🔑 ใส่ Groq API Key:", type="password", help="รับฟรีที่ console.groq.com")
    
    # อัปเดตรายชื่อโมเดลที่ Groq รองรับ ณ ปัจจุบัน
    MODEL_NAME = st.selectbox(
        "ชื่อโมเดล (Groq):", 
        [
            "llama-3.3-70b-versatile",    # ตัวหลัก ฉลาดและเร็วมาก
            "llama-3.1-8b-instant",       # ตัวรอง เร็วปานสายฟ้า
            "mixtral-8x7b-32768"          # ตัวเลือกเสริม เก่งคณิตศาสตร์
        ]
    )
    st.caption("💡 แนะนำให้ใช้ llama-3.3-70b-versatile เป็นหลักครับ")

    response_style = st.selectbox(
        "รูปแบบการตอบของ AI:",
        ["📝 สอนและอธิบายละเอียด", "⚡️ เฉลยอย่างเดียว (กระชับ)"],
        key="style_memory"
    )

    st.divider()

    st.header("📤 อัปโหลดเอกสาร/รูปภาพ")
    uploaded_file = st.file_uploader("แนบไฟล์ PDF, TXT หรือรูปโจทย์", type=["pdf", "txt", "png", "jpg", "jpeg"])

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

    if st.button("🗑️ ล้างแชท", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# -----------------------------------------
# 4. แสดงประวัติแชทบนหน้าจอ
# -----------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "image_show" in message:
            st.image(message["image_show"], width=300)

        content = message["content"]
        if message["role"] == "assistant" and "</think>" in str(content):
            parts = str(content).split("</think>")
            with st.expander("💡 ดูเบื้องหลังการคิด"):
                st.write(parts[0].replace("<think>", "").strip())
            st.markdown(fix_latex(parts[1].strip()))
        else:
            st.markdown(fix_latex(content))

        if "plot" in message:
            st.pyplot(message["plot"])

# -----------------------------------------
# 5. รับข้อความ & จัดการข้อมูลให้ตรงตามกฎแต่ละโมเดล
# -----------------------------------------
if prompt := st.chat_input("พิมพ์โจทย์ หรือสั่งให้ AI วิเคราะห์..."):
    
    if not API_KEY.strip():
        st.error("⚠️ กรุณาใส่ Groq API Key ที่แถบด้านซ้ายก่อนครับ!")
        st.stop()

    # บันทึกโจทย์ที่ผู้ใช้พิมพ์โชว์บนหน้าจอ
    user_msg = {"role": "user", "content": prompt}
    if uploaded_img:
        user_msg["image_show"] = uploaded_img
    
    st.session_state.messages.append(user_msg)
    
    with st.chat_message("user"):
        if uploaded_img:
            st.image(uploaded_img, width=300)
        st.markdown(prompt)

    # เริ่มเรียกใช้งาน AI
    with st.chat_message("assistant"):
        try:
            client = Groq(api_key=API_KEY.strip())
            
            # --- ระบบสับราง (ดักจับประเภทโมเดล) ---
            is_deepseek = "deepseek" in MODEL_NAME.lower()
            is_vision = "vision" in MODEL_NAME.lower()

            # แยกร่างคำสั่งให้ต่างกันแบบสุดขั้ว
            if "อธิบายละเอียด" in response_style:
                sys_prompt = """คุณคืออาจารย์คณิตศาสตร์ระดับมหาวิทยาลัย (โหมดอธิบายละเอียด)
                กฎเหล็ก (ต้องทำตามอย่างเคร่งครัด):
                1. อธิบายเหมือนสอนนักเรียนที่พื้นฐานอ่อน ต้องบอกเหตุผลเสมอว่า 'ทำไมถึงใช้สูตรนี้' หรือ 'ตัวแปรนี้มาจากไหน'
                2. แบ่งโครงสร้างชัดเจน: **1. วิเคราะห์โจทย์**, **2. แสดงวิธีทำ**, **3. สรุปคำตอบ**
                3. ห้ามแปล Integral ว่า "ค่าอนันต์" (ให้ใช้คำว่า อินทิเกรต หรือ หาปริพันธ์)
                4. บังคับใช้ LaTeX ครอบสมการทุกครั้ง ($...$ สำหรับในบรรทัด, $$...$$ สำหรับแยกบรรทัด)
                5. ตอบเฉพาะข้อที่ผู้ใช้สั่ง ห้ามทำข้ออื่นแถม"""
            else:
                sys_prompt = """คุณคือเครื่องคิดเลขคณิตศาสตร์ (โหมดสมการเพียว ไร้คำบรรยาย)
                กฎเหล็ก (ต้องทำตามอย่างเคร่งครัด):
                1. ห้ามเขียนคำบรรยายภาษาไทย ห้ามมีหัวข้อ ห้ามมีคำอธิบายทฤษฎีใดๆ ทั้งสิ้น (ยกเว้นคำว่า "คำตอบสุดท้าย:")
                2. ให้แสดงเฉพาะบรรทัดสมการทางคณิตศาสตร์เรียงต่อกันลงมาเรื่อยๆ จนจบ
                3. บังคับใช้ LaTeX แบบจัดเรียงสมการ (Aligned) โดยครอบด้วย $$ เสมอ เช่น:
                $$ \begin{aligned} \int x \cos(4x) dx &= ... \\ &= ... \\ &= ... \end{aligned} $$
                4. บรรทัดล่างสุดให้พิมพ์แค่ **คำตอบสุดท้าย:** ตามด้วยสมการ
                5. ตอบเฉพาะข้อที่ผู้ใช้สั่ง ห้ามทำข้ออื่นแถม"""

            messages_for_ai = []
            
            # กฎข้อ 1: ถ้าไม่ใช่ DeepSeek ถึงจะอนุญาตให้ส่ง System Prompt ได้
            if not is_deepseek:
                messages_for_ai.append({'role': 'system', 'content': sys_prompt})

            # นำประวัติแชทมาเรียบเรียงใหม่
            for i, m in enumerate(st.session_state.messages):
                role = m['role']
                content_text = str(m['content'])
                
                # กฎข้อ 2: ถ้าเป็น DeepSeek ให้แอบยัดคำสั่ง System ไว้ในข้อความแรกของผู้ใช้แทน
                if is_deepseek and i == 0 and role == 'user':
                    content_text = f"[คำสั่งระบบ: {sys_prompt}]\n\n" + content_text

                # กฎข้อ 3: จัดการไฟล์และรูปภาพ เฉพาะกับคำถาม "ข้อล่าสุด" เท่านั้น
                if i == len(st.session_state.messages) - 1 and role == 'user':
                    if file_content:
                        content_text += f"\n\n[ข้อมูลอ้างอิงจากไฟล์]:\n{file_content}"
                    
                    if base64_image:
                        if is_vision:
                            # กฎข้อ 4: รูปแบบ JSON พิเศษสำหรับโมเดล Vision โดยเฉพาะ
                            payload = [
                                {"type": "text", "text": content_text},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                            ]
                            messages_for_ai.append({'role': role, 'content': payload})
                            continue # ข้ามการ append แบบ text ปกติไปเลย
                        else:
                            content_text += "\n\n(ผู้ใช้แนบรูปมาด้วย แต่โมเดลนี้ไม่รองรับการดูรูปภาพ ให้คุณตอบจากข้อความโจทย์เป็นหลัก)"

                messages_for_ai.append({'role': role, 'content': content_text})

            full_response = ""
            is_thinking = False
            answer_placeholder = st.empty()
            start_time = time.time()

            # ส่งยิงขึ้น Cloud
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

            # วาดกราฟอัตโนมัติ
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
            # ดัก Error มาโชว์ให้เห็นชัดๆ เลยว่าพังเพราะอะไร
            st.error(f"🚨 Cloud Error: {e}")