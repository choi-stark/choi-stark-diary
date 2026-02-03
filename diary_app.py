import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import requests
import random

# 페이지 설정
st.set_page_config(page_title="최본부장님의 미라클 다이어리", layout="wide")

# 1. 스타일 설정 (달력 동그라미 표기 등)
st.markdown("""
    <style>
    .fc-daygrid-event { border-radius: 50% !important; background-color: rgba(255, 0, 0, 0.2) !important; border: none !important; }
    .stButton>button { width: 100%; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 구글 시트 연결 및 데이터 로드
conn = st.connection("gsheets", type=GSheetsConnection)
def get_data():
    return conn.read(worksheet="Sheet1")

df = get_data()

# 3. 세션 상태 초기화 (단계별 입력을 위해)
if 'step' not in st.session_state:
    st.session_state.step = 1

# --- 메인 화면 구성 ---
tab1, tab2 = st.tabs(["일기 작성", "지난 기록 (달력)"])

# ---------------- Tab 1: 일기 작성 ----------------
with tab1:
    st.title("🚀 오늘의 감사 & 확언 프로세스")

    # STEP 1: 감사일기 작성
    if st.session_state.step == 1:
        st.header("🙏 1단계: 감사일기 작성")
        g1 = st.text_input("오늘 감사한 일 1")
        g2 = st.text_input("오늘 감사한 일 2")
        g3 = st.text_input("오늘 감사한 일 3")
        
        if st.button("감사 에너지 분석 및 다음 단계"):
            if g1 and g2 and g3:
                # [크롤링 대용] 감사 명언 API 또는 라이브러리 활용
                response = requests.get("https://korean-advice-open-api.vercel.app/api/advice")
                st.session_state.g_quote = response.json()['message'] if response.status_code == 200 else "감사는 마음의 근육을 강화합니다."
                st.session_state.g_data = [g1, g2, g3]
                st.session_state.step = 2
                st.rerun()
            else:
                st.warning("3가지를 모두 작성해 주세요.")

    # STEP 2: 감사 분석 결과 & 확언 작성
    elif st.session_state.step == 2:
        st.success(f"✅ 감사 분석 완료: {st.session_state.g_quote}")
        st.write("---")
        st.header("✨ 2단계: 확언일기 작성")
        a1 = st.text_input("나의 확언 1")
        a2 = st.text_input("나의 확언 2")
        a3 = st.text_input("나의 확언 3")

        if st.button("확신 메시지 받기 및 저장"):
            if a1 and a2 and a3:
                # [크롤링 대용] 확신 멘트 및 이미지 크롤링 시뮬레이션
                st.session_state.a_data = [a1, a2, a3]
                st.session_state.step = 3
                st.rerun()

    # STEP 3: 최종 결과 확인 및 저장
    elif st.session_state.step == 3:
        st.header("🎁 오늘의 통찰과 이미지")
        
        # 이미지 크롤링 (Unsplash 소스 활용)
        img_url = f"https://source.unsplash.com/featured/?meditation,nature&sig={random.randint(1,1000)}"
        st.image(img_url, caption="오늘 본부장님의 에너지를 담은 이미지")
        
        meaning = "이 이미지는 본부장님의 확언이 우주에 전달되어 단단한 뿌리를 내리는 과정을 상징합니다."
        st.info(f"💡 이미지의 의미: {meaning}")
        
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
            st.success("오늘의 기록이 완벽하게 저장되었습니다!")
            st.rerun()

# ---------------- Tab 2: 지난 기록 (달력) ----------------
with tab2:
    st.header("📅 다이어리 기록 달력")
    
    # 달력 이벤트 데이터 생성
    calendar_events = []
    for i, row in df.iterrows():
        calendar_events.append({
            "title": "●",
            "start": row["날짜"],
            "end": row["날짜"],
            "color": "#FFCCCC"  # 연한 붉은색
        })

    # 달력 표시
    selected_date = calendar(events=calendar_events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}})
    
    # 날짜 클릭 시 해당 일기 표시
    if "callback" in selected_date and selected_date["callback"] == "dateClick":
        clicked_date = selected_date["dateClick"]["dateStr"]
        day_data = df[df["날짜"] == clicked_date]
        
        if not day_data.empty:
            st.write(f"### 🗓️ {clicked_date}의 기록")
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🙏 감사")
                st.write(f"- {day_data.iloc[0]['감사1']}\n- {day_data.iloc[0]['감사2']}\n- {day_data.iloc[0]['감사3']}")
            with col2:
                st.subheader("✨ 확언")
                st.write(f"- {day_data.iloc[0]['확언1']}\n- {day_data.iloc[0]['확언2']}\n- {day_data.iloc[0]['확언3']}")
            st.image(day_data.iloc[0]['이미지URL'], width=300)
            st.caption(day_data.iloc[0]['의미'])
        else:
            st.info("해당 날짜에 작성된 일기가 없습니다.")
