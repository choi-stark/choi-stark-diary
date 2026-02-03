import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import requests
import random

# 페이지 설정
st.set_page_config(page_title="미라클 다이어리", layout="wide")

# 1. 스타일 설정 (달력 동그라미 및 UI 커스텀)
st.markdown("""
    <style>
    /* 달력 이벤트(동그라미) 스타일 */
    .fc-daygrid-event { 
        border-radius: 50% !important; 
        width: 10px !important; 
        height: 10px !important; 
        margin: 0 auto !important;
        background-color: rgba(255, 0, 0, 0.4) !important; 
        border: none !important; 
    }
    .stButton>button { width: 100%; border-radius: 20px; }
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

# 세션 상태 초기화
if 'step' not in st.session_state:
    st.session_state.step = 1

# --- 메인 화면 구성 ---
tab1, tab2 = st.tabs(["일기 작성", "지난 기록 (달력)"])

# ---------------- Tab 1: 일기 작성 ----------------
with tab1:
    st.title("✍️ 오늘의 감사 & 확언")

    # STEP 1: 감사일기
    if st.session_state.step == 1:
        st.header("🙏 1단계: 감사일기 작성")
        g1 = st.text_input("오늘 감사한 일 1")
        g2 = st.text_input("오늘 감사한 일 2")
        g3 = st.text_input("오늘 감사한 일 3")
        
        # 버튼 명칭 '제출'로 변경
        if st.button("제출"):
            if g1 and g2 and g3:
                try:
                    response = requests.get("https://korean-advice-open-api.vercel.app/api/advice")
                    st.session_state.g_quote = response.json()['message'] if response.status_code == 200 else "감사는 삶을 풍요롭게 합니다."
                except:
                    st.session_state.g_quote = "오늘도 감사한 하루입니다."
                st.session_state.g_data = [g1, g2, g3]
                st.session_state.step = 2
                st.rerun()
            else:
                st.warning("3가지를 모두 작성해 주세요.")

    # STEP 2: 확언일기
    elif st.session_state.step == 2:
        st.info(f"💡 분석 메시지: {st.session_state.g_quote}")
        st.write("---")
        st.header("✨ 2단계: 확언일기 작성")
        a1 = st.text_input("나의 확언 1")
        a2 = st.text_input("나의 확언 2")
        a3 = st.text_input("나의 확언 3")

        if st.button("확신 메시지 받기 및 저장"):
            if a1 and a2 and a3:
                st.session_state.a_data = [a1, a2, a3]
                st.session_state.step = 3
                st.rerun()

    # STEP 3: 최종 결과
    elif st.session_state.step == 3:
        st.header("🎁 오늘의 통찰")
        img_url = f"https://picsum.photos/seed/{random.randint(1,1000)}/800/400"
        st.image(img_url, caption="오늘의 에너지 이미지")
        meaning = "당신의 확언이 현실이 되는 과정입니다."
        st.info(f"💡 의미: {meaning}")
        
        if st.button("최종 저장하기"):
            new_entry = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "이미지URL": img_url, "의미": meaning
            }])
            updated_df = pd.concat([df, new_entry], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.balloons()
            st.session_state.step = 1
            st.success("저장 완료!")
            st.rerun()

# ---------------- Tab 2: 지난 기록 (달력) ----------------
with tab2:
    st.header("📅 다이어리 기록 달력")
    
    # 달력 이벤트 설정
    calendar_events = []
    if not df.empty:
        for i, row in df.iterrows():
            calendar_events.append({
                "title": "●",
                "start": str(row["날짜"]),
                "end": str(row["날짜"]),
                "display": "block",
                "color": "rgba(255, 0, 0, 0.2)"
            })

    # 달력 옵션 보강 (달력이 보이지 않는 문제 해결용)
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth"
        },
        "initialView": "dayGridMonth",
        "selectable": "true",
    }

    # 달력 표시
    state = calendar(events=calendar_events, options=calendar_options, key='diary_calendar')
    
    if state.get("callback") == "dateClick":
        clicked_date = state["dateClick"]["dateStr"]
        day_data = df[df["날짜"] == clicked_date]
        
        if not day_data.empty:
            st.write(f"### 🗓️ {clicked_date}의 기록")
            st.write(f"**감사:** {day_data.iloc[0]['감사1']}, {day_data.iloc[0]['감사2']}, {day_data.iloc[0]['감사3']}")
            st.write(f"**확언:** {day_data.iloc[0]['확언1']}, {day_data.iloc[0]['확언2']}, {day_data.iloc[0]['확언3']}")
            st.image(day_data.iloc[0]['이미지URL'], width=400)
