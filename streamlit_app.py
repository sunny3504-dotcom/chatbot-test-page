import streamlit as st
from openai import OpenAI
import os, re
from pathlib import Path

st.set_page_config(page_title="야식 챗봇 — GPT", page_icon="🍜")

# -----------------------------------
# CSS
# -----------------------------------
st.markdown("""
<style>
textarea::placeholder {
    font-size: 13px;
    color: #bfbfbf !important;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------
# Header
# -----------------------------------
st.title("🍜 야식 추천 챗봇")
st.write("안녕하세요. 야식(심야) 추천에 특화된 챗봇입니다")

placeholder_text = (
    "야식 챗봇에게 어떤 야식을 먹으면 좋을지 질문해보세요. "
    "간단한 설명과 주문/요리 팁을 포함하여 세 가지 맞춤형 메뉴를 제안해 드립니다. "
    "필요 시 선호하는 메뉴(매운맛, 예산, 시간, 식단 제한 등)에 대한 명확한 질문을 하세요."
)

# -----------------------------------
# Default System Prompt
# -----------------------------------
default_system_prompt = (
    "You are a friendly assistant specialized in recommending late-night snacks (야식). "
    "Provide 3 tailored menu suggestions with descriptions and cooking tips. "
    "Ask clarifying questions when needed. Always answer in Korean."
)

# -----------------------------------
# SESSION INIT
# -----------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": default_system_prompt}
    ]

# -----------------------------------
# API KEY
# -----------------------------------
def load_api_key():
    if "OPENAI_API_KEY" in st.secrets:
        return st.secrets["OPENAI_API_KEY"]
    if os.getenv("OPENAI_API_KEY"):
        return os.getenv("OPENAI_API_KEY")
    try:
        t = Path(".streamlit/secrets.toml").read_text()
        m = re.search(r'OPENAI_API_KEY\s*=\s*["\']?([^"\']+)["\']?', t)
        if m:
            return m.group(1).strip()
    except:
        pass
    return None

api_key = load_api_key()
if not api_key:
    st.error("❗ OpenAI API 키가 없습니다.")
    st.stop()

client = OpenAI(api_key=api_key)

# -----------------------------------
# SINGLE INPUT FORM (버튼 포함)
# -----------------------------------
with st.form("chat_form", clear_on_submit=True):
    user_prompt = st.text_area(
        "",
        placeholder=placeholder_text,
        height=150
    )
    submit = st.form_submit_button("챗봇에게 물어보기")   # ← 버튼 문구 변경 완료

# -----------------------------------
# PROCESS
# -----------------------------------
if submit and user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    try:
        with st.spinner("추천 생성 중…"):
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages
            )

        assistant_msg = resp.choices[0].message.content

    except Exception as e:
        assistant_msg = f"API 오류: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})

# -----------------------------------
# RENDER CHAT
# -----------------------------------
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
