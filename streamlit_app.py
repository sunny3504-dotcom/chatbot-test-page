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
# 상단 제목 및 설명
# -------------------------------------------------
st.title("🍜 야식 추천 챗봇")
st.write("안녕하세요. 야식(심야) 추천에 특화된 챗봇입니다")

# -------------------------------------------------
# placeholder 및 기본 시스템 프롬프트
# -------------------------------------------------
placeholder_text = (
    "야식 추천 요청 또는 시스템 프롬프트를 입력하세요.\n"
    "예: '매콤한 야식 추천해줘'"
)

default_system_prompt = (
    "You are a friendly, concise assistant specialized in recommending late-night snacks (야식). "
    "Provide 3 tailored menu suggestions with short descriptions and cooking tips. "
    "Ask clarifying questions when needed. Always answer in Korean."
)

# -------------------------------------------------
# 세션 상태 초기화
# -------------------------------------------------
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = default_system_prompt

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": st.session_state.system_prompt}
    ]

# -------------------------------------------------
# API 키 로딩
# -------------------------------------------------
def _load_api_key() -> str | None:
    try:
        key = st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except:
        pass

    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key

    try:
        p = Path(".streamlit/secrets.toml")
        if p.exists():
            text = p.read_text(encoding="utf-8")
            m = re.search(r'OPENAI_API_KEY\s*=\s*["\']?([^"\'\n]+)["\']?', text)
            if m:
                return m.group(1).strip()
    except:
        pass

    return None

api_key = _load_api_key()
if not api_key:
    st.error("OpenAI API 키가 설정되지 않았습니다.", icon="❗")
    st.stop()

client = OpenAI(api_key=api_key)

# -------------------------------------------------
# GPT 응답 파싱 함수
# -------------------------------------------------
def _get_choice_text(resp: Any) -> str:
    try:
        return resp.choices[0].message["content"]
    except:
        return str(resp)

# -------------------------------------------------
# 프롬프트 입력창 + 버튼 (하나만 사용)
# -------------------------------------------------
with st.form(key="unified_form", clear_on_submit=True):
    prompt_text = st.text_area(
        "",
        placeholder=placeholder_text,
        height=140
    )
    submit_btn = st.form_submit_button("전송 / 적용")

# -------------------------------------------------
# 처리 로직 (시스템 프롬프트 수정 + 사용자 질문 처리)
# -------------------------------------------------
if submit_btn and prompt_text:

    # 1) 시스템 프롬프트 수정
    if prompt_text.startswith(("프롬프트:", "system:", "prompt:")):
        new_prompt = prompt_text.split(":", 1)[1].strip()
        st.session_state.system_prompt = new_prompt
        st.session_state.messages[0]["content"] = new_prompt
        st.success("시스템 프롬프트가 수정되었습니다!")

    # 2) 일반 사용자 질문 → GPT 대답
    else:
        st.session_state.messages.append({"role": "user", "content": prompt_text})

        with st.chat_message("user"):
            st.write(prompt_text)

        try:
            with st.spinner("추천 생성 중…"):
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=st.session_state.messages,
                    max_tokens=500,
                    temperature=0.8
                )
            answer = _get_choice_text(resp)
        except Exception as e:
            answer = f"API 오류: {e}"

        st.session_state.messages.append({"role": "assistant", "content": answer})

        with st.chat_message("assistant"):
            st.markdown(answer)

# -------------------------------------------------
# 기존 대화 출력 (system 제외)
# -------------------------------------------------
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
