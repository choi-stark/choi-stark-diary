import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import random

# 페이지 설정
st.set_page_config(page_title="미라클 다이어리", layout="wide")

# 1. 스타일 설정 (달력 가시성 및 UI 커스텀)
st.markdown("""
    <style>
    .fc-daygrid-event { 
        border-radius: 50% !important; 
        width: 12px !important; 
        height: 12px !important; 
        margin: 0 auto !important;
        background-color: #FF4B4B !important; 
        border: none !important; 
    }
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; height: 3em; }
    .stHeader { color: #1E1E1E; }
    </style>
    """, unsafe_allow_html=True)

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        return conn.read(worksheet="Sheet1")
    except:
        return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "이미지URL", "의미"])

df = get_data()

# 강력한 확신 메시지 리스트
RESOLUTE_MESSAGES = [
    "신은 본부장님의 신호를 이미 접수하셨습니다. 모든 것은 계획대로 이루어지고 있습니다.",
    "오늘 본부장님의 하루는 온전히 본부장님의 것입니다. 우주가 당신의 행보를 지지합니다.",
    "말하는 대로 이루어지는 우주의 법칙이 지금 이 순간 본부장님을 향해 흐르고 있습니다.",
    "이미 목적지에 도착한 것처럼 행동하십시오. 당신의 결의가 현실을 창조하고 있습니다.",
    "오늘의 모든 에너지는 본부장님의 성공을 위해 정렬되었습니다. 단단하게 나아가십시오."
]

# 세션 상태 초기화
if 'step' not in st.session_state:
    st.session_state.step = 1

# --- 메인 화면 구성 ---
tab1, tab2 = st.tabs(["일기 작성", "지난 기록 (달력)"])

# ---------------- Tab 1: 일기 작성 ----------------
with tab1:
    st.title("🔥 최본부장님의 결의 다이어리")

    # STEP 1: 감사일기
    if st.session_state.step == 1:
        st.header("🙏 1단계: 감사일기 작성")
        g1 = st.text_input("오늘 감사
