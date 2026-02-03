import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import google.generativeai as genai
import random

# 1. 페이지 설정
st.set_page_config(page_title="미라클 다이어리", layout="wide")

# 2. 스타일 설정 (달력 가시성 확보)
st.markdown("""
    <style>
    .fc-daygrid-event { border-radius: 50% !important; width: 14px !important; height: 14px !important; margin: 2px auto !important; background-color: #FF0000 !important; border: none !important; }
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; height: 3.5em; }
    .stSuccess { font-size: 1.1em; font-weight: bold; border-left: 5px solid #FF4B4B; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 연결 및 AI 설정
conn = st.connection("gsheets", type=GSheetsConnection)

if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets 설정을 확인해주세요.")
    st.stop()

# 데이터 로드 함수 (에러를 숨기지 않고 표시합니다)
def get_data(force_refresh=False):
    ttl = 0 if force_refresh else 600
    try:
        return conn.read(worksheet="Sheet1", ttl=ttl)
    except Exception as e:
        st.error(f"❌ 구글 시트 연결 에러: {e}")
        return pd.DataFrame()

# AI 결의 멘트 생성 함수
def ask_gemini(prompt, role_type="mentor"):
    role = "인생 멘토" if role_type == "mentor" else "우주의 전령"
    try:
        response = model.generate_content(f"당신은 {role}입니다. 최본부장님에게 단호하고 강력한 결의의 2문장을 주세요: {prompt}")
        return response.text
    except:
        return "당신의 결의는 이미 우주에 닿았습니다. 오늘 하루는 당신의 것입니다."

# 4. 세션 상태 초기화
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
                with st.spinner('신의 신호를 읽는 중...'):
                    st.session_state.g_comment = ask_gemini(f"감사 내용: {g1}, {g2}, {g3}")
                    st.session_state.g_data = [g1, g2, g3]
                    st.session_state.step = 2
                    st.rerun()

    elif st.session_state.step == 2:
        # 감사일기에 대한 코멘트 표시 (복구 완료)
        st.success(f"✨ 오늘의 메시지: {st.session_state.g_comment}")
        
        st.header("✨ 2단계: 확언일기 작성")
        a1 = st.text_input("강력한 확언 1", key="a1")
        a2 = st.text_input("강력한 확언 2", key="a2")
        a3 = st.text_input("강력한 확언 3", key="a3")
        if st.button("제출 "):
            if a1 and a2 and a3:
                with st.spinner('확신의 답변을 가져오는 중...'):
                    st.session_state.a_comment = ask_gemini(f"확언 내용: {a1}, {a2}, {a3}", "universal")
                    st.session_state.a_data = [a1, a2, a3]
                    st.session_state.step = 3
                    st.rerun()

    elif st.session_state.step == 3:
        st.header("🎁 우주의 응답")
        # 확언에 대한 확신 멘트 표시
        st.info(f"💫 확신 멘트: {st.session_state.a_comment}")
        
        img_url = f"https://picsum.photos/seed/{st.session_state.img_seed}/1200/600"
        st.image(img_url, use_container_width=True)
        
        if 'img_meaning' not in st.session_state:
            st.session_state.img_meaning = ask_gemini(f"이 사진({img_url})이 본부장님의 결의와 어떤 의미가 있는지 한 줄로.")
        st.write(f"💡 이미지의 의미: {st.session_state.img_meaning}")
        
        if st.button("최종 기록 제출"):
            new_entry = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes", "이미지URL": img_url, "의미": st.session_state.img_meaning
            }])
            try:
                # 저장 시 최신 데이터 합치기
                current_df = conn.read(worksheet="Sheet1", ttl=0)
                updated_df = pd.concat([current_df, new_entry], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.balloons()
                st.session_state.step = 1
                # 상태 초기화
                for key in ['g_comment', 'a_comment', 'img_meaning', 'img_seed']:
                    if key in st.session_state: del st.session_state[key]
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"저장 중 오류 발생: {e}")

# ---------------- Tab 2: 지난 기록 ----------------
with tab2:
    st.header("📅 지난 기록")
    
    # 동기화 버튼 클릭 시 강제로 데이터를 다시 읽어옵니다.
    if st.button("🔄 최신 기록으로 동기화"):
        st.cache_data.clear()
        st.rerun()

    df = get_data()

    if df.empty or len(df) == 0:
        st.info("아직 기록된 일기가 없습니다. 첫 기록을 제출해 보세요!")
    else:
        # 달력 이벤트 설정
        events = [{"title": "●", "start": str(row["날짜"]), "end": str(row["날짜"]), "display": "background", "color": "rgba(255, 0, 0, 0.4)"} for _, row in df.iterrows()]
        
        state = calendar(events=events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "initialView": "dayGridMonth", "height": 700}, key='miracle_calendar_vfinal')
        
        if state.get("callback") == "dateClick":
            clicked_date = state["dateClick"]["dateStr"]
            day_data = df[df["날짜"] == clicked_date]
            if not day_data.empty:
                st.markdown("---")
                st.markdown(f"### 🗓️ {clicked_date}의 기록")
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🙏 감사")
                    st.write(f"1. {day_data.iloc[0]['감사1']}\n2. {day_data.iloc[0]['감사2']}\n3. {day_data.iloc[0]['감사3']}")
                with col2:
                    st.subheader("✨ 확언")
                    st.write(f"1. {day_data.iloc[0]['확언1']}\n2. {day_data.iloc[0]['확언2']}\n3. {day_data.iloc[0]['확언3']}")
                st.image(day_data.iloc[0]['이미지URL'], use_container_width=True)
                st.info(f"💡 의미: {day_data.iloc[0]['의미']}")
