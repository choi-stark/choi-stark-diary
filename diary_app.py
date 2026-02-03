import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import google.generativeai as genai
import random

# 1. 페이지 설정 및 스타일 (달력 시각화 보강)
st.set_page_config(page_title="미라클 다이어리", layout="wide")
st.markdown("""
    <style>
    .fc-daygrid-event { border-radius: 50% !important; width: 14px !important; height: 14px !important; margin: 2px auto !important; background-color: #FF0000 !important; border: none !important; }
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

# 2. API 및 데이터 연결 (캐시 완전 제거)
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    try:
        # ttl=0으로 설정하여 매번 구글 시트에서 직접 새 데이터를 가져옵니다.
        return conn.read(worksheet="Sheet1", ttl=0)
    except:
        # 에러 발생 시 시트 헤더 구조를 가진 빈 데이터프레임 생성
        return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "사진여부", "이미지URL", "의미"])

# 앱 시작 시 최신 데이터 로드
df = get_data()

# 3. 제미나이 AI 설정 (NotFound 에러 방지)
if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    # 가장 안정적인 모델명으로 고정
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets에 'gemini_api_key'가 없습니다.")
    st.stop()

def ask_gemini(prompt):
    try:
        response = model.generate_content(f"당신은 인생 멘토입니다. 단호하고 확신에 찬 2문장의 결의 멘트를 주세요: {prompt}")
        return response.text
    except:
        return "당신의 결의가 우주에 닿았습니다. 오늘 하루는 온전히 당신의 것입니다."

# 4. 세션 상태 초기화 (사진 및 단계 고정)
if 'step' not in st.session_state: st.session_state.step = 1
if 'img_seed' not in st.session_state: st.session_state.img_seed = random.randint(1, 9999)

tab1, tab2 = st.tabs(["오늘의 일기작성", "지난 기록"])

# ---------------- Tab 1: 오늘의 일기작성 ----------------
with tab1:
    if st.session_state.step == 1:
        st.header("🙏 1단계: 감사일기")
        g1 = st.text_input("감사 1", key="g1")
        g2 = st.text_input("감사 2", key="g2")
        g3 = st.text_input("감사 3", key="g3")
        if st.button("제출"):
            if g1 and g2 and g3:
                st.session_state.g_data = [g1, g2, g3]
                st.session_state.step = 2
                st.rerun()

    elif st.session_state.step == 2:
        st.header("✨ 2단계: 확언일기")
        a1 = st.text_input("확언 1", key="a1")
        a2 = st.text_input("확언 2", key="a2")
        a3 = st.text_input("확언 3", key="a3")
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
            with st.spinner('메시지 생성 중...'):
                st.session_state.meaning = ask_gemini(f"감사:{st.session_state.g_data}, 확언:{st.session_state.a_data}")
        st.info(f"💡 메시지: {st.session_state.meaning}")
        
        if st.button("최종 기록 제출"):
            new_entry = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes", "이미지URL": img_url, "의미": st.session_state.meaning
            }])
            try:
                # 저장 직전 최신 데이터를 다시 읽어와서 병합
                fresh_df = get_data()
                final_df = pd.concat([fresh_df, new_entry], ignore_index=True)
                conn.update(worksheet="Sheet1", data=final_df)
                
                # 모든 캐시 강제 삭제 및 초기화
                st.cache_data.clear()
                st.balloons()
                st.session_state.step = 1
                del st.session_state.img_seed
                del st.session_state.meaning
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패! 시트 설정을 확인하세요: {e}")

# ---------------- Tab 2: 지난 기록 (달력) ----------------
with tab2:
    st.header("📅 지난 기록")
    # 수동 새로고침 버튼으로 동기화 보장
    if st.button("🔄 최신 기록 가져오기"):
        st.cache_data.clear()
        st.rerun()

    if df.empty or len(df) == 0:
        st.info("아직 기록된 일기가 없습니다. 첫 기록을 제출해 보세요!")
    else:
        events = [{"title": "●", "start": str(row["날짜"]), "end": str(row["날짜"]), "display": "background", "color": "rgba(255, 0, 0, 0.4)"} for _, row in df.iterrows()]
        
        state = calendar(events=events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "initialView": "dayGridMonth", "height": 700}, key='miracle_calendar_final')
        
        if state.get("callback") == "dateClick":
            clicked_date = state["dateClick"]["dateStr"]
            day_data = df[df["날짜"] == clicked_date]
            if not day_data.empty:
                st.markdown(f"---")
                st.markdown(f"### 🗓️ {clicked_date}의 기록")
                st.write(f"🙏 **감사**: {day_data.iloc[0]['감사1']}, {day_data.iloc[0]['감사2']}, {day_data.iloc[0]['감사3']}")
                st.write(f"✨ **확언**: {day_data.iloc[0]['확언1']}, {day_data.iloc[0]['확언2']}, {day_data.iloc[0]['확언3']}")
                st.image(day_data.iloc[0]['이미지URL'])
                st.info(f"💡 **의미**: {day_data.iloc[0]['의미']}")
