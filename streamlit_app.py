import streamlit as st
from openai import OpenAI
import os
import re
from pathlib import Path

st.set_page_config(page_title="야식 챗봇 — GPT", page_icon="🍜")

# -------------------------------------------------
# UI 스타일
# -------------------------------------------------
st.markdown(
    """
    <style>
        textarea::placeholder {
            font-size: 13px;
            color: #bfbfbf !important;
        }
        div[data-testid="chat-message"][data-testid="chat-message-system"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------------------------------
# 상단 제목
# -------------------------------------------------
st.title("🍜 야식 추천 챗봇")
st.write("안녕하세요. 야식(심야) 추천에 특화된 챗봇입니다")

# -------------------------------------------------
# placeholder 문구
# -------------------------------------------------
placeholder_text = (
    "야식 챗봇에게 어떤 야식을 먹으면 좋을지 질문해보세요. "
    "간단한 설명과 주문/요리 팁을 포함하여 세 가지 맞춤형 메뉴를 제안해 드립니다. "
    "필요 시 선호하는 메뉴(매운맛, 예산, 시간, 식단 제한 등)에 대한 명확한 질문을 하세요."
)

# -------------------------------------------------
# 기본 시스템 프롬프트
# -------------------------------------------------
default_system_prompt = (
    "You are a friendly, concise assistant specialized in recommending late-night snacks (야식). "
    "Provide 3 tailored menu suggestions with descriptions and cooking tips. "
    "Ask clarifying questions when needed. Always answer in Korean."
)

# -------------------------------------------------
# 세션 초기화
# -------------------------------------------------
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = default_system_prompt

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": st.session_state.system_prompt}
    ]

# -------------------------------------------------
# API KEY 가져오기
# -------------------------------------------------
def load_api_key():
    try:
        key = st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except:
        pass

    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]

    try:
        t = Path(".streamlit/secrets.toml").read_text(encoding="utf-8")
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

# -------------------------------------------------
# 입력창
# -------------------------------------------------
with st.form(key="chat_form", clear_on_submit=True):
    prompt_text = st.text_area("", placeholder=placeholder_text, height=150)
    send_btn = st.form_submit_button("챗봇에게 물어보기")

# -------------------------------------------------
# GPT 호출 + 로직 처리
# -------------------------------------------------
if send_btn and prompt_text:

    # 시스템 프롬프트 수정 모드
    if prompt_text.startswith(("프롬프트:", "prompt:", "system:")):
        new_prompt = prompt_text.split(":", 1)[1].strip()
        st.session_state.system_prompt = new_prompt
        st.session_state.messages[0] = {"role": "system", "content": new_prompt}
        st.success("시스템 프롬프트가 수정되었습니다!")

    else:
        # 사용자 메시지 추가
        st.session_state.messages.append({"role": "user", "content": prompt_text})

        with st.chat_message("user"):
            st.write(prompt_text)

        # GPT API 호출
        try:
            with st.spinner("추천 생성 중…"):
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages,
                    max_tokens=500
                )

            # 최신 SDK 구조: message.content
            assistant_msg = resp.choices[0].message.content  

        except Exception as e:
            assistant_msg = f"API 오류: {e}"

        # assistant 메시지 저장
        st.session_state.messages.append(
            {"role": "assistant", "content": assistant_msg}
        )

# -------------------------------------------------
# 채팅 기록 출력
# -------------------------------------------------
for m in st.session_state.messages:
    if m["role"] == "system":
        continue

    with st.chat_message(m["role"]):
        st.markdown(m["content"])
