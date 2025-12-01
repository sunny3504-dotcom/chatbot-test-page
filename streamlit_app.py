import streamlit as st
from openai import OpenAI
from typing import Any
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
        /* placeholder 스타일 */
        textarea::placeholder {
            font-size: 13px;
            color: #bfbfbf !important;
        }

        /* system 메시지를 강제로 숨기는 CSS (백업용) */
        div[data-testid="chat-message"][data-testid="chat-message-system"] {
            display: none !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# -------------------------------------------------
# 상단 제목 및 설명
# -------------------------------------------------
st.title("🍜 야식 추천 챗봇")
st.write("안녕하세요. 야식(심야) 추천에 특화된 챗봇입니다")


# -------------------------------------------------
# 시스템 프롬프트 placeholder
# -------------------------------------------------
placeholder_text = (
    "야식(심야) 추천에 특화된 챗봇입니다. 간단한 설명과 주문/요리 팁을 포함하여 세 가지 맞춤형 메뉴를 제안해 드립니다. "
    "필요 시 선호하는 메뉴(매운맛, 예산, 시간, 식단 제한 등)에 대한 명확한 질문을 하세요. "
    "사용자가 별도로 요청하지 않는 한 답변은 한국어로 작성해 주세요."
)

default_system_prompt = (
    "You are a friendly, concise assistant specialized in recommending late-night snacks (야식). "
    "Provide 3 tailored menu suggestions with short descriptions and ordering/cooking tips. "
    "Ask clarifying questions about preferences (spiciness, budget, time, dietary restrictions) when needed. "
    "Keep answers in Korean unless the user asks otherwise."
)


# -------------------------------------------------
# session_state 초기화
# -------------------------------------------------
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = default_system_prompt

if "messages" not in st.session_state:
    # system 메시지는 API 호출용으로만 보관. 화면에는 절대 표시하지 않음.
    st.session_state.messages = [
        {"role": "system", "content": st.session_state.system_prompt}
    ]


# -------------------------------------------------
# 시스템 프롬프트 입력 UI
# -------------------------------------------------
with st.form(key="system_prompt_form", clear_on_submit=False):
    prompt_input = st.text_area(
        label="",         # "시스템 프롬프트" 글자 제거
        value="",         # textarea 내부 영어 기본값 제거
        placeholder=placeholder_text,
        height=140,
    )
    apply_btn = st.form_submit_button("적용")

    if apply_btn:
        # 비어 있으면 placeholder 내용 그대로 system prompt 로 사용
        if prompt_input.strip() == "":
            st.session_state.system_prompt = placeholder_text
        else:
            st.session_state.system_prompt = prompt_input

        # system 메시지를 항상 messages[0]에 반영
        st.session_state.messages[0]["content"] = st.session_state.system_prompt

        st.success("시스템 프롬프트가 적용되었습니다!")


# -------------------------------------------------
# API KEY LOAD
# -------------------------------------------------
def _get_choice_text(resp: Any) -> str:
    try:
        return resp.choices[0].message["content"]
    except:
        return str(resp)


def _load_api_key() -> str | None:
    try:
        if st.secrets.get("OPENAI_API_KEY"):
            return st.secrets.get("OPENAI_API_KEY")
    except:
        pass

    if os.environ.get("OPENAI_API_KEY"):
        return os.environ.get("OPENAI_API_KEY")

    try:
        text = Path(".streamlit/secrets.toml").read_text(encoding="utf-8")
        m = re.search(r'OPENAI_API_KEY\s*=\s*["\']?([^"\'\n]+)["\']?', text)
        if m:
            return m.group(1).strip()
    except:
        pass

    return None


api_key = _load_api_key()
if not api_key:
    st.error("OpenAI API 키가 설정되어 있지 않습니다.", icon="❗")
    st.stop()

client = OpenAI(api_key=api_key)


# -------------------------------------------------
# 기존 메시지 렌더링 (system 메시지는 절대 화면에 출력하지 않음)
# -------------------------------------------------
for m in st.session_state.messages:
    if m["role"] == "system":
        continue  # 👈 system 메시지는 화면에 표시하지 않고 API용으로만 사용
    with st.chat_message(m["role"]):
        st.markdown(m["content"])


# -------------------------------------------------
# 사용자 입력
# -------------------------------------------------
user_prompt = st.chat_input("무슨 야식이 먹고 싶으세요? (예: 매콤한/담백한, 배달/직접조리, 예산 등)")

if user_prompt:
    # 화면 표시
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # GPT 호출
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.messages,
        temperature=0.8,
        max_tokens=500,
    )

    assistant_text = _get_choice_text(response)

    # assistant 메시지 저장
    st.session_state.messages.append({"role": "assistant", "content": assistant_text})

    # 화면 출력
    with st.chat_message("assistant"):
        st.markdown(assistant_text)
