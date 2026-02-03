import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import google.generativeai as genai
import random

# 1. 페이지 설정 및 스타일
st.set_page_config(page_title="미라클 다이어리", layout="wide")
st.markdown("""
    <style>
    .fc-daygrid-event { border-radius: 50% !important; width: 14px !important; height: 14px !important; margin: 2px auto !important; background-color: #FF0000 !important; border: none !important; }
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; height: 3.5em; }
    .stSuccess { font-size: 1.2em; font-weight: bold; border-left: 8px solid #FF4B4B; background-color: #FFF5F5; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 연결 및 AI 설정 (NotFound 에러 방지용 모델명 적용)
conn = st.connection("gsheets", type=GSheetsConnection)

if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    # 🎯 모델 이름을 가장 최신 버전인 'gemini-1.5-flash-latest'로 수정했습니다.
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
else:
    st.error("Secrets 설정을 확인해주세요.")
    st.stop()

# 최신 데이터를 읽어오는 함수 (캐시를 0초로 설정하여 즉시 반영)
def get_data():
    try:
        return conn.read(worksheet="Sheet1", ttl=0)
    except Exception as e:
        return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "사진여부", "이미지URL", "의미"])

# 3. 세션 상태 초기화 (사진 고정 및 단계 관리)
if 'step' not in st.session_state: st.session_state.step = 1
if 'img_seed' not in st.session_state: st.session_state.img_seed = random.randint(1, 9999)
if 'g_comment' not in st.session_state: st.session_state.g_comment = ""
if 'a_comment' not in st.session_state: st.session_state.a_comment = ""

# AI 결의 멘트 생성 함수
def ask_gemini(prompt):
    try:
        response = model.generate_content(f"당신은 단호한 인생 멘토입니다. 최본부장님의 일기를 보고 결의의 2문장을 주세요: {prompt}")
        return response.text
    except Exception as e:
        # 에러 발생 시 부드러운 대체 문구를 출력합니다.
        return f"당신의 의지가 현실을 만듭니다. 오늘 하루는 온전히 당신의 것입니다."

tab1, tab2 = st.tabs(["오늘의 일기작성", "지난 기록"])

# ---------------- Tab 1: 오늘의 일기작성 ----------------
with tab1:
    if st.session_state.step == 1:
        st.header("🙏 1단계: 감사일기 작성")
        g1 = st.text_input("감사 1", key="g1")
        g2 = st.text_input("감사 2", key="g2")
        g3 = st.text_input("감사 3", key="g3")
        if st.button("제출"):
            if g1 and g2 and g3:
                with st.spinner('제미나이가 메시지를 작성 중...'):
                    st.session_state.g_comment = ask_gemini(f"감사: {g1}, {g2}, {g3}")
                    st.session_state.g_data = [g1, g2, g3]
                    st.session_state.step = 2
                    st.rerun()

    elif st.session_state.step == 2:
        # 🎯 AI 코멘트 노출 (감사일기 답변)
        st.success(f"🤖 제미나이의 멘토링: \n\n {st.session_state.g_comment}")
        
        st.header("✨ 2단계: 확언일기 작성")
        a1 = st.text_input("확언 1", key="a1")
        a2 = st.text_input("확언 2", key="a2")
        a3 = st.text_input("확언 3", key="a3")
        if st.button("제출 "):
            if a1 and a2 and a3:
                with st.spinner('우주의 확신을 가져오는 중...'):
                    st.session_state.a_comment = ask_gemini(f"확언: {a1}, {a2}, {a3}")
                    st.session_state.a_data = [a1, a2, a3]
                    st.session_state.step = 3
                    st.rerun()

    elif st.session_state.step == 3:
        # 🎯 AI 코멘트 노출 (확언 답변)
        st.info(f"💫 확신 멘트: \n\n {st.session_state.a_comment}")
        
        img_url = f"https://picsum.photos/seed/{st.session_state.img_seed}/1200/600"
        st.image(img_url, use_container_width=True)
        
        if 'img_meaning' not in st.session_state:
            st.session_state.img_meaning = ask_gemini(f"이 사진({img_url})의 의미를 한 줄로.")
        st.write(f"💡 이미지의 의미: {st.session_state.img_meaning}")
        
        if st.button("최종 기록 제출"):
            new_row = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes", "이미지URL": img_url, "의미": st.session_state.img_meaning
            }])
            try:
                # 저장 직전 실시간 데이터를 합칩니다.
                fresh_df = conn.read(worksheet="Sheet1", ttl=0)
                updated_df = pd.concat([fresh_df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.balloons()
                st.cache_data.clear() # 모든 캐시 삭제
                st.session_state.step = 1
                # 데이터 정리
                for k in ['g_comment', 'a_comment', 'img_meaning', 'img_seed']:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

# ---------------- Tab 2: 지난 기록 (달력) ----------------
with tab2:
    st.header("📅 지난 기록")
    if st.button("🔄 실시간 동기화"):
        st.cache_data.clear()
        st.rerun()

    df = get_data() # 항상 실시간 데이터를 읽어옵니다.

    if df.empty or len(df) == 0:
        st.info("기록된 일기가 없습니다. 첫 일기를 작성해 보세요!")
    else:
        events = [{"title": "●", "start": str(row["날짜"]), "end": str(row["날짜"]), "display": "background", "color": "red"} for _, row in df.iterrows()]
        
        cal = calendar(events=events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "initialView": "dayGridMonth", "height": 700}, key='miracle_cal_final')
        
        if cal.get("callback") == "dateClick":
            date_str = cal["dateClick"]["dateStr"]
            target = df[df["날짜"] == date_str]
            if not target.empty:
                st.markdown("---")
                st.subheader(f"🗓️ {date_str}의 기록")
                st.write(f"🙏 **감사**: {target.iloc[0]['감사1']}, {target.iloc[0]['감사2']}, {target.iloc[0]['감사3']}")
                st.write(f"✨ **확언**: {target.iloc[0]['확언1']}, {target.iloc[0]['확언2']}, {target.iloc[0]['확언3']}")
                st.image(target.iloc[0]['이미지URL'])
