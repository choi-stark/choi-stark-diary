import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import google.generativeai as genai
import random

# 1. 페이지 설정
st.set_page_config(page_title="미라클 다이어리", layout="wide")

# 2. API 및 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 로딩 함수 (과부하 방지를 위해 1분간 기억/캐시 설정)
@st.cache_data(ttl=60)
def get_data():
    try:
        # worksheet 이름을 "Sheet1"으로 고정하여 읽어옵니다.
        return conn.read(worksheet="Sheet1")
    except:
        return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "사진여부", "이미지URL", "의미"])

# AI 설정
if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets 설정을 확인해주세요.")
    st.stop()

def ask_gemini(prompt):
    try:
        response = model.generate_content(f"당신은 단호한 인생 멘토입니다. 2문장 결의 메시지: {prompt}")
        return response.text
    except:
        return "당신의 결의가 우주에 닿았습니다. 오늘 하루는 온전히 당신의 것입니다."

# 세션 초기화
if 'step' not in st.session_state: st.session_state.step = 1
if 'img_seed' not in st.session_state: st.session_state.img_seed = random.randint(1, 9999)

tab1, tab2 = st.tabs(["오늘의 일기작성", "지난 기록"])

# ---------------- Tab 1: 오늘의 일기작성 ----------------
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
            with st.spinner('메시지 생성 중...'):
                st.session_state.meaning = ask_gemini(f"감사:{st.session_state.g_data}, 확언:{st.session_state.a_data}")
        st.info(f"💡 이미지의 의미: {st.session_state.meaning}")
        
        if st.button("최종 기록 제출"):
            new_entry = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes", "이미지URL": img_url, "의미": st.session_state.meaning
            }])
            try:
                # 저장할 때만 캐시를 무시하고 읽어옵니다.
                current_df = conn.read(worksheet="Sheet1", ttl=0)
                updated_df = pd.concat([current_df, new_entry], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                # 저장 성공 시 모든 기억(캐시) 초기화
                st.cache_data.clear()
                st.balloons()
                st.session_state.step = 1
                del st.session_state.img_seed
                del st.session_state.meaning
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

# ---------------- Tab 2: 지난 기록 (달력) ----------------
with tab2:
    st.header("📅 지난 기록")
    # 기록이 즉시 안 보일 때만 사용하세요.
    if st.button("🔄 최신 기록으로 동기화"):
        st.cache_data.clear()
        st.rerun()

    # 데이터를 불러옵니다.
    df = get_data()

    if df.empty or len(df) == 0:
        st.info("아직 기록된 일기가 없습니다. 첫 일기를 작성해 보세요!")
    else:
        events = [{"title": "●", "start": str(row["날짜"]), "end": str(row["날짜"]), "display": "background", "color": "rgba(255, 0, 0, 0.4)"} for _, row in df.iterrows()]
        
        state = calendar(events=events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "initialView": "dayGridMonth", "height": 700}, key='miracle_calendar_final')
        
        if state.get("callback") == "dateClick":
            clicked_date = state["dateClick"]["dateStr"]
            day_data = df[df["날짜"] == clicked_date]
            if not day_data.empty:
                st.markdown(f"---")
                st.markdown(f"### 🗓️ {clicked_date}의 기록")
                st.write(f"🙏 감사: {day_data.iloc[0]['감사1']}, {day_data.iloc[0]['감사2']}, {day_data.iloc[0]['감사3']}")
                st.write(f"✨ 확언: {day_data.iloc[0]['확언1']}, {day_data.iloc[0]['확언2']}, {day_data.iloc[0]['확언3']}")
                st.image(day_data.iloc[0]['이미지URL'])
