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
    /* AI 코멘트 박스 스타일 */
    .stSuccess { font-size: 1.2em; font-weight: bold; border-left: 8px solid #FF4B4B; background-color: #FFF5F5; }
    </style>
    """, unsafe_allow_html=True)

# 2. 연결 및 AI 설정
conn = st.connection("gsheets", type=GSheetsConnection)

if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets에 'gemini_api_key'가 없습니다. 설정을 확인해주세요.")
    st.stop()

# 데이터 로드 함수 (기본 1분 캐시, 새로고침 시 ttl=0)
def get_data(ttl_value=60):
    try:
        return conn.read(worksheet="Sheet1", ttl=ttl_value)
    except Exception as e:
        st.error(f"시트 읽기 실패: {e}")
        return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "사진여부", "이미지URL", "의미"])

# AI 메시지 생성 함수
def ask_gemini(prompt):
    try:
        response = model.generate_content(f"당신은 단호한 인생 멘토입니다. 최본부장님의 일기를 보고 강력한 결의의 2문장을 주세요: {prompt}")
        return response.text
    except Exception as e:
        return f"우주의 기운이 당신과 함께합니다. (오류: {str(e)[:50]})"

# 세션 상태 초기화
if 'step' not in st.session_state: st.session_state.step = 1
if 'img_seed' not in st.session_state: st.session_state.img_seed = random.randint(1, 9999)

tab1, tab2 = st.tabs(["오늘의 일기작성", "지난 기록"])

# ---------------- Tab 1: 오늘의 일기작성 ----------------
with tab1:
    # --- 1단계: 감사일기 ---
    if st.session_state.step == 1:
        st.header("🙏 1단계: 감사일기 작성")
        g1 = st.text_input("감사 1", key="input_g1")
        g2 = st.text_input("감사 2", key="input_g2")
        g3 = st.text_input("감사 3", key="input_g3")
        if st.button("제미나이에게 감사 보내기"):
            if g1 and g2 and g3:
                with st.spinner('제미나이가 생각 중입니다...'):
                    st.session_state.g_data = [g1, g2, g3]
                    st.session_state.g_comment = ask_gemini(f"감사한 일: {g1}, {g2}, {g3}")
                    st.session_state.step = 2
                    st.rerun()

    # --- 2단계: 확언일기 ---
    elif st.session_state.step == 2:
        # 🎯 AI 코멘트 노출 (감사일기 답변)
        st.success(f"🤖 제미나이의 멘토링: \n\n {st.session_state.g_comment}")
        
        st.header("✨ 2단계: 확언일기 작성")
        a1 = st.text_input("확언 1", key="input_a1")
        a2 = st.text_input("확언 2", key="input_a2")
        a3 = st.text_input("확언 3", key="input_a3")
        if st.button("제미나이에게 확언 보내기"):
            if a1 and a2 and a3:
                with st.spinner('우주의 기운을 모으는 중...'):
                    st.session_state.a_data = [a1, a2, a3]
                    st.session_state.a_comment = ask_gemini(f"오늘의 확언: {a1}, {a2}, {a3}")
                    st.session_state.step = 3
                    st.rerun()

    # --- 3단계: 최종 확인 및 제출 ---
    elif st.session_state.step == 3:
        st.info(f"💫 확신 멘트: \n\n {st.session_state.a_comment}")
        
        img_url = f"https://picsum.photos/seed/{st.session_state.img_seed}/1200/600"
        st.image(img_url, use_container_width=True)
        
        if 'img_meaning' not in st.session_state:
            st.session_state.img_meaning = ask_gemini(f"이미지({img_url})의 의미 해석 한 줄")
        st.write(f"💡 이미지의 의미: {st.session_state.img_meaning}")
        
        if st.button("🔥 오늘의 결의 최종 제출"):
            new_row = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes", "이미지URL": img_url, "의미": st.session_state.img_meaning
            }])
            try:
                # 즉시 쓰기 및 캐시 강제 무력화
                current_df = conn.read(worksheet="Sheet1", ttl=0)
                updated_df = pd.concat([current_df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.balloons()
                st.cache_data.clear() # 전체 캐시 삭제
                st.session_state.step = 1
                # 세션 데이터 정리
                for key in ['g_comment', 'a_comment', 'img_meaning', 'img_seed']:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

# ---------------- Tab 2: 지난 기록 (달력) ----------------
with tab2:
    st.header("📅 지난 기록")
    
    # 🔄 수동 동기화 버튼 (ttl=0 강제 적용)
    if st.button("🔄 시트와 실시간 동기화"):
        st.cache_data.clear()
        st.rerun()

    # 최신 데이터를 가져옵니다.
    df = get_data(ttl_value=0 if st.session_state.get('refresh') else 60)

    if df.empty:
        st.info("기록된 데이터가 없습니다. 첫 일기를 작성해 보세요!")
    else:
        # 달력 이벤트
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
