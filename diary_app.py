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

# --- 데이터를 실시간(ttl=0)으로 읽어오는 함수 ---
def get_data():
    try:
        # ttl=0 설정을 통해 캐시를 무시하고 항상 최신 시트 내용을 가져옵니다.
        return conn.read(worksheet="Sheet1", ttl=0)
    except:
        return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "이미지URL", "의미"])

# 앱 시작 시 데이터 로드
df = get_data()

def ask_gemini(prompt):
    system_instruction = "당신은 인생 멘토입니다. 매우 단호하고 확신에 찬 어조로 2~3문장의 결의 메시지를 작성하세요."
    try:
        response = model.generate_content(f"{system_instruction}\n\n내용: {prompt}")
        return response.text
    except:
        return "당신의 의지가 현실을 창조합니다. 오늘 하루를 당신의 것으로 만드십시오."

if 'step' not in st.session_state: st.session_state.step = 1

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
                with st.spinner('신의 신호를 읽어오는 중...'):
                    st.session_state.g_quote = ask_gemini(f"감사: {g1}, {g2}, {g3}")
                st.session_state.g_data = [g1, g2, g3]
                st.session_state.step = 2
                st.rerun()

    elif st.session_state.step == 2:
        st.success(f"✨ 오늘의 메시지: {st.session_state.g_quote}")
        st.header("✨ 2단계: 확언일기 작성")
        a1 = st.text_input("강력한 확언 1", key="a1")
        a2 = st.text_input("강력한 확언 2", key="a2")
        a3 = st.text_input("강력한 확언 3", key="a3")

        if st.button("제출 "):
            if a1 and a2 and a3:
                with st.spinner('우주의 확신을 가져오는 중...'):
                    st.session_state.a_quote = ask_gemini(f"확언: {a1}, {a2}, {a3}")
                st.session_state.a_data = [a1, a2, a3]
                st.session_state.step = 3
                st.rerun()

    elif st.session_state.step == 3:
        st.header("🎁 우주의 응답")
        st.info(f"💫 확신 멘트: {st.session_state.a_quote}")
        img_url = f"https://picsum.photos/seed/{random.randint(1,9999)}/1200/600"
        st.image(img_url, use_container_width=True)
        
        meaning = ask_gemini(f"이 사진({img_url})의 의미를 본부장님의 결의와 연결해 한 줄로 설명해줘.")
        st.write(f"💡 이미지의 의미: {meaning}")
        
        if st.button("최종 기록 제출"):
            new_entry = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "이미지URL": img_url, "의미": meaning
            }])
            
            # 최신 데이터를 다시 불러와서 합칩니다.
            current_df = get_data()
            updated_df = pd.concat([current_df, new_entry], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            
            st.balloons()
            st.session_state.step = 1
            # 즉시 새로고침하여 반영합니다.
            st.cache_data.clear()
            st.rerun()

# ---------------- Tab 2: 지난 기록 (실시간 반영) ----------------
with tab2:
    st.header("📅 지난 결의 기록")
    
    # 탭 이동 시 최신 데이터 강제 로드
    if st.button("🔄 기록 새로고침"):
        st.cache_data.clear()
        st.rerun()

    if df.empty or len(df) == 0:
        st.info("아직 작성된 일기가 없습니다. 첫 일기를 작성해 보세요!")
    else:
        calendar_events = []
        for _, row in df.iterrows():
            calendar_events.append({
                "title": "●",
                "start": str(row["날짜"]),
                "end": str(row["날짜"]),
                "display": "background",
                "color": "rgba(255, 0, 0, 0.4)"
            })

        state = calendar(
            events=calendar_events, 
            options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "initialView": "dayGridMonth", "height": 700}, 
            key='miracle_calendar_final'
        )
        
        if state.get("callback") == "dateClick":
            clicked_date = state["dateClick"]["dateStr"]
            day_data = df[df["날짜"] == clicked_date]
            if not day_data.empty:
                st.markdown(f"---")
                st.markdown(f"### 🗓️ {clicked_date}의 기록")
                st.write(f"🙏 감사: {day_data.iloc[0]['감사1']}, {day_data.iloc[0]['감사2']}, {day_data.iloc[0]['감사3']}")
                st.write(f"✨ 확언: {day_data.iloc[0]['확언1']}, {day_data.iloc[0]['확언2']}, {day_data.iloc[0]['확언3']}")
                st.image(day_data.iloc[0]['이미지URL'])
