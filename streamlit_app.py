import streamlit as st
from openai import OpenAI
from typing import Any
import os
import re
from pathlib import Path

st.set_page_config(page_title="야식 챗봇 — GPT", page_icon="🍜")

st.title("🍜 야식 추천 챗봇")
st.write(
    "야식(심야) 추천에 특화된 챗봇입니다. 간단한 설명과 주문/요리 팁을 포함하여 세 가지 맞춤형 메뉴를 제안해 드립니다. 필요 시 선호하는 메뉴(매운맛, 예산, 시간, 식단 제한 등)에 대한 명확한 질문을 하세요. 사용자가 별도로 요청하지 않는 한 답변은 한국어로 작성해 주세요."
)

# --- 시스템 프롬프트 편집 UI (요청사항: 제목 바로 아래에 배치) ---
default_system_prompt = (
    "You are a friendly, concise assistant specialized in recommending late-night snacks (야식). "
    "Provide 3 tailored menu suggestions with short descriptions and ordering/cooking tips. "
    "Ask clarifying questions about preferences (spiciness, budget, time, dietary restrictions) when needed. "
    "Keep answers in Korean unless the user asks otherwise."
)

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = default_system_prompt

with st.form(key="system_prompt_form", clear_on_submit=False):
    prompt_input = st.text_area(
        label="시스템 프롬프트",
        value=st.session_state.get("system_prompt", ""),
        placeholder=st.session_state.get("system_prompt", ""),
        height=140,
    )
    apply_btn = st.form_submit_button("적용")
    if apply_btn:
        # 저장 및 messages[0]의 system 업데이트
        st.session_state.system_prompt = prompt_input
        if "messages" in st.session_state and len(st.session_state.messages) > 0 and st.session_state.messages[0].get("role") == "system":
            st.session_state.messages[0]["content"] = prompt_input
        else:
            # ensure system message exists at index 0
            st.session_state.messages = [{"role": "system", "content": prompt_input}] + st.session_state.get("messages", [])
        st.success("시스템 프롬프트가 적용되었습니다.")


def _get_choice_text(resp: Any) -> str:
    try:
        choice = resp.choices[0]
        # choice.message may be dict-like or object-like
        if hasattr(choice, "message"):
            msg = choice.message
            return getattr(msg, "content", msg.get("content") if isinstance(msg, dict) else str(msg))
        # fallback
        return str(choice)
    except Exception:
        return str(resp)


def _load_api_key() -> str | None:
    # 1) Try Streamlit secrets
    try:
        key = st.secrets.get("OPENAI_API_KEY")
        if key:
            return key
    except Exception:
        pass

    # 2) Try environment variable
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key

    # 3) Try reading .streamlit/secrets.toml (accept quoted or unquoted value)
    try:
        p = Path(".streamlit/secrets.toml")
        if p.exists():
            text = p.read_text(encoding="utf-8")
            m = re.search(r'OPENAI_API_KEY\s*=\s*["\']?([^"\'\n]+)["\']?', text)
            if m:
                return m.group(1).strip()
    except Exception:
        pass

    return None


api_key = _load_api_key()
if not api_key:
    st.error(
        "OpenAI API 키가 설정되어 있지 않습니다. `.streamlit/secrets.toml`에 `OPENAI_API_KEY = \"your_key\"` 형태로 추가하거나 환경변수 `OPENAI_API_KEY`를 설정하세요.",
        icon="❗",
    )
    st.stop()

client = OpenAI(api_key=api_key)


# Initialize chat history with a system prompt focused on late-night snack recommendations
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "You are a friendly, concise assistant specialized in recommending late-night snacks (야식). "
                "Provide 3 tailored menu suggestions with short descriptions and ordering/cooking tips. "
                "Ask clarifying questions about preferences (spiciness, budget, time, dietary restrictions) when needed. "
                "Keep answers in Korean unless the user asks otherwise."
            ),
        }
    ]


# Render existing messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])


# Chat input: no API key input (per requirements), direct use
user_prompt = st.chat_input("무슨 야식이 먹고 싶으세요? (예: 매콤한/담백한, 배달/직접조리, 예산 등)")
if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    messages_for_api = [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    try:
        with st.spinner("추천을 생성 중입니다…"):
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_for_api,
                max_tokens=500,
                temperature=0.8,
            )
        assistant_text = _get_choice_text(resp)
    except Exception as e:
        st.error(f"OpenAI API 호출 중 오류가 발생했습니다: {e}")
        assistant_text = "죄송합니다. 응답 생성에 실패했습니다. 잠시 후 다시 시도해주세요."

    st.session_state.messages.append({"role": "assistant", "content": assistant_text})
    with st.chat_message("assistant"):
        st.markdown(assistant_text)
