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
        /* system 메시지 숨기기 */
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

# -------------------------------------------------
# 시스템 프롬프트 입력 UI (단 하나만 남김)
# -------------------------------------------------
with st.form(key="system_prompt_form", clear_on_submit=False):
    prompt_input = st.text_area(
        label="",  
        value="",  
        placeholder=placeholder_text,
        height=140,
    )
    apply_btn = st.form_submit_button("적용")

    if apply_btn:
        if prompt_input.strip() == "":
            st.session_state.system_prompt = placeholder_text
        else:
            st.session_state.system_prompt = prompt_input

        st.success("시스템 프롬프트가 적용되었습니다!")


# -------------------------------------------------
# 여기에 있었던 사용자 입력창과 챗봇 대화 로직 전체 제거됨
# -------------------------------------------------

