import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import google.generativeai as genai
import random

# 페이지 설정
st.set_page_config(page_title="미라클 다이어리", layout="wide")

# 1. 스타일 설정
st.markdown("""
    <style>
    .fc-daygrid-event { border-radius: 50% !important; width: 14px !important; height: 14px !important; margin: 2px auto !important; background-color: #FF0000 !important; border: none !important; }
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; height: 3.5em; }
    .stSuccess { font-size: 1.1em; font-weight: bold; border-left: 5px solid #FF4B4B; }
    </style>
    """, unsafe_allow_html=True)

# 2. API 및 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets에 'gemini_api_key'를 설정해주세요.")
    st.stop()

def get_data():
    try:
        # worksheet 이름을 "Sheet1"으로 고정하고 캐시를 제거합니다.
        return conn.read(worksheet="Sheet1", ttl=0)
    except:
        return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "사진여부", "이미지URL", "의미"])

df = get_data()

# 세션 상태 초기화 (사진 고정용)
if 'step' not in st.session_state: st.session_state.step = 1
if 'img_seed' not in st.session_state: st.session_state.img_seed = random.randint(1, 9999)

tab1, tab2 = st.tabs(["오늘의 일기작성", "지난 기록"])

# ---------------- Tab 1: 일기 작성 ----------------
with tab1:
    if st.session_state.step == 1:
        st.header("🙏 1단계: 감사일기 작성")
        g1 = st.text_input("오늘 감사한 일 1", key="g1")
        g2 = st.text_input("오늘 감사한 일 2", key="g2")
        g3 = st.text_input("오늘 감사한 일 3", key="g3")
        if st.button("제출"):
            if g1 and g2 and g3:
                st.session_state.g_data = [g1, g2, g3]
                st.session_state.step = 2
                st.rerun()

    elif st.session_state.step == 2:
        st.header("✨ 2단계: 확언일기 작성")
        a1 = st.text_input("강력한 확언 1", key="a1")
        a2 = st.text_input("강력한 확언 2", key="a2")
        a3 = st.text_input("강력한 확언 3", key="a3")
        if st.button("제출 "):
            if a1 and a2 and a3:
                st.session_state.a_data = [a1, a2, a3]
                st.session_state.step = 3
                st.rerun()

    elif st.session_state.step == 3:
        st.header("🎁 우주의 응답")
        img_url = f"https://picsum.photos/seed/{st.session_state.img_seed}/1200/600"
        st.image(img_url, use_container_width=True)
        
        if 'meaning' not in st.session_state:
            with st.spinner('메시지를 생성 중입니다...'):
                prompt = f"이 사진({img_url})의 의미를 본부장님의 일기와 연결해 한 줄로 설명해줘."
                st.session_state.meaning = model.generate_content(prompt).text
        st.info(f"💡 이미지의 의미: {st.session_state.meaning}")
        
        if st.button("최종 기록 제출"):
            # 시트의 헤더(날짜~의미)와 순서를 완벽히 맞춘 데이터 생성
            new_entry = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes", # 시트의 사진여부 칸을 채웁니다.
                "이미지URL": img_url,
