import streamlit as st
from openai import OpenAI
import os
import re
from pathlib import Path

st.set_page_config(page_title="야식 챗봇 — GPT", page_icon="🍜")

# ----------------------------------------------
# CSS
# ----------------------------------------------
st.markdown(
    """
    <style>
        textarea::placeholder {
            font-size: 13px;
            color: #bfbfbf !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------------------------
# Header
# ----------------------------------------------
st.title("🍜 야식 추천 챗봇")
st.write("안녕하세요. 야식(심야) 추천에 특화된 챗봇입니다")

placeholder_text = (
    "야식 챗봇에게 어떤 야식을 먹으면 좋을지 질문해보세요. "
    "간단한 설명과 주문/요리 팁을 포함하여 세 가지 맞춤형 메뉴를 제안해 드립니다. "
    "필요 시 선호하는 메뉴(매운맛, 예산, 시간, 식단 제한 등)에 대한 명확한 질문을 하세요."
)

# ----------------------------------------------
# Default System prompt
# ----------------------------------------------
default_system_prompt = (
    "You are a friendly assistant specialized in recommending late-night snacks (야식). "
    "Provide 3 tailored menu suggestions with descriptions and cooking tips. "
    "Ask clarifying questions when needed. Always answer in Korean."
)

# ----------------------------------------------
# Session State Init
# ----------------------------------------------
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = default_system_prompt

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": st.session_state.system_prompt}
    ]

# ----------------------------------------------
# API Key Load
# ----------------------------------------------
def load_api_key():
    if st.secrets.get("OPENAI_API_KEY"):
        return st.secrets["OPENAI_API_KEY"]

    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]

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

# ----------------------------------------------
# INPUT FORM
# ----------------------------------------------
with st.form("chat_form", clear_on_submit=True):
    user_prompt = st.text_area("", placeholder=placeholder_text, height=150)
    submitted = st.form_submit_button("챗봇에게 물어보기")

# ----------------------------------------------
# CHAT LOGIC
# ----------------------------------------------
if submitted and user_prompt:

    if user_prompt.startswith(("프롬프트:", "system:", "prompt:")):
        new_prompt = user_prompt.split(":", 1)[1].strip()
        st.session_state.system_prompt = new_prompt
        st.session_state.messages[0] = {"role": "system", "content": new_prompt}
        st.success("시스템 프롬프트가 수정되었습니다!")

    else:
        st.session_state.messages.append({"role": "user", "content": user_prompt})

        try:
            with st.spinner("답변 생성 중…"):
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages
                )

            assistant_msg = resp.choices[0].message.content

        except Exception as e:
            assistant_msg = f"API 오류: {str(e)}"

        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_msg}
        )

# ----------------------------------------------
# RENDER CHAT
# ----------------------------------------------
for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue

    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
