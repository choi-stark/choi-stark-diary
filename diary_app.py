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

# Secrets 위치 확인 및 모델 설정 (가장 안정적인 모델명 사용)
if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    # 모델명을 가장 범용적인 것으로 변경했습니다.
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets의 맨 윗줄에 'gemini_api_key'를 설정해주세요.")
    st.stop()

def get_data():
    try: return conn.read(worksheet="Sheet1", ttl=0)
    except: return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "사진여부", "이미지URL", "의미"])

df = get_data()

# AI에게 메시지 요청 (에러 방지 로직 추가)
def ask_gemini(prompt):
    system_instruction = "당신은 인생 멘토입니다. 매우 단호하고 확신에 찬 어조로 2문장 내외의 결의 메시지를 작성하세요."
    try:
        response = model.generate_content(f"{system_instruction}\n\n내용: {prompt}")
        return response.text
    except Exception as e:
        # 에러 발생 시 부드러운 대체 문구 제공
        return "당신의 의지가 곧 현실이 됩니다. 오늘 하루는 온전히 당신의 것입니다."

# 세션 상태 초기화 (사진 고정을 위해)
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
        
        # --- 사진 고정: 한 번 생성된 시드값으로 고정합니다 ---
        img_url = f"https://picsum.photos/seed/{st.session_state.img_seed}/1200/600"
        st.image(img_url, use_container_width=True)
        
        # 의미 해석 (에러 방지 포함)
        if 'meaning' not in st.session_state:
            with st.spinner('메시지 생성 중...'):
                st.session_state.meaning = ask_gemini(f"이 사진({img_url})의 의미를 본부장님의 일기와 연결해줘.")
        st.info(f"💡 이미지의 의미: {st.session_state.meaning}")
        
        if st.button("최종 기록 제출"):
            new_entry = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes",
                "이미지URL": img_url, 
                "의미": st.session_state.meaning
            }])
            try:
                current_df = get_data()
                updated_df = pd.concat([current_df, new_entry], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                st.balloons()
                st.session_state.step = 1
                # 저장 성공 시 사진 정보 초기화 (다음 기록을 위해)
                del st.session_state.img_seed
                if 'meaning' in st.session_state: del st.session_state.meaning
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

# ---------------- Tab 2: 지난 기록 ----------------
with tab2:
    st.header("📅 지난 결의 기록")
    if st.button("🔄 기록 새로고침"):
        st.cache_data.clear()
        st.rerun()

    if df.empty:
        st.info("아직 기록된 일기가 없습니다.")
    else:
        calendar_events = [{"title": "●", "start": str(row["날짜"]), "end": str(row["날짜"]), "display": "background", "color": "rgba(255, 0, 0, 0.4)"} for _, row in df.iterrows()]
        calendar(events=calendar_events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "initialView": "dayGridMonth", "height": 700}, key='miracle_calendar_final')
