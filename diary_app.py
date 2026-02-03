import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import google.generativeai as genai
import random

# 1. 페이지 설정
st.set_page_config(page_title="미라클 다이어리", layout="wide")

# 2. 시스템 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 로딩 함수 (과부하 방지를 위해 20분간 데이터를 기억합니다)
@st.cache_data(ttl=1200)
def get_data():
    try:
        # worksheet 이름을 "Sheet1"으로 고정하여 읽어옵니다.
        return conn.read(worksheet="Sheet1")
    except Exception as e:
        if "429" in str(e):
            st.error("⚠️ 구글 서버가 아직 휴식 중입니다. 5분 뒤에 다시 시도해 주세요.")
        return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "사진여부", "이미지URL", "의미"])

# AI 설정 (안정적인 모델명 사용)
if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets 설정을 확인해주세요.")
    st.stop()

def ask_gemini(prompt):
    try:
        response = model.generate_content(f"단호한 인생 멘토로서 2문장 결의 메시지: {prompt}")
        return response.text
    except:
        return "당신의 의지가 곧 현실입니다. 전진하십시오."

# 세션 상태 관리
if 'step' not in st.session_state: st.session_state.step = 1
if 'img_seed' not in st.session_state: st.session_state.img_seed = random.randint(1, 9999)

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
                st.session_state.g_comment = ask_gemini(f"감사: {g1}, {g2}, {g3}")
                st.session_state.g_data = [g1, g2, g3]
                st.session_state.step = 2
                st.rerun()

    elif st.session_state.step == 2:
        st.success(f"🤖 제미나이: {st.session_state.g_comment}")
        st.header("✨ 2단계: 확언일기 작성")
        a1 = st.text_input("확언 1", key="a1")
        a2 = st.text_input("확언 2", key="a2")
        a3 = st.text_input("확언 3", key="a3")
        if st.button("제출 "):
            if a1 and a2 and a3:
                st.session_state.a_comment = ask_gemini(f"확언: {a1}, {a2}, {a3}")
                st.session_state.a_data = [a1, a2, a3]
                st.session_state.step = 3
                st.rerun()

    elif st.session_state.step == 3:
        st.info(f"💫 확신: {st.session_state.a_comment}")
        img_url = f"https://picsum.photos/seed/{st.session_state.img_seed}/1200/600"
        st.image(img_url, use_container_width=True)
        
        if 'img_meaning' not in st.session_state:
            st.session_state.img_meaning = ask_gemini(f"이미지({img_url})의 의미 해석")
        st.write(f"💡 의미: {st.session_state.img_meaning}")
        
        if st.button("🔥 최종 기록 제출"):
            new_row = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes", "이미지URL": img_url, "의미": st.session_state.img_meaning
            }])
            try:
                # 저장 시에만 최소한의 호출을 수행합니다.
                current_df = conn.read(worksheet="Sheet1", ttl=0)
                updated_df = pd.concat([current_df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                st.balloons()
                st.cache_data.clear() # 저장 후에만 캐시를 지웁니다.
                st.session_state.step = 1
                for k in ['g_comment', 'a_comment', 'img_meaning', 'img_seed']:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ 저장 중 과부하가 발생했습니다. 잠시 후 다시 시도하세요. ({e})")

# ---------------- Tab 2: 지난 기록 (달력) ----------------
with tab2:
    st.header("📅 지난 기록")
    
    # 데이터를 불러옵니다 (20분간 캐시된 데이터를 사용해 서버 호출을 최소화합니다).
    df = get_data()

    if st.button("🔄 기록 강제 새로고침 (하루 한두 번만 권장)"):
        st.cache_data.clear()
        st.rerun()

    if not df.empty and len(df) > 0:
        events = [{"title": "●", "start": str(row["날짜"]), "end": str(row["날짜"]), "display": "background", "color": "red"} for _, row in df.iterrows()]
        cal = calendar(events=events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "initialView": "dayGridMonth", "height": 700}, key='miracle_calendar')
        
        if cal.get("callback") == "dateClick":
            date_str = cal["dateClick"]["dateStr"]
            target = df[df["날짜"] == date_str]
            if not target.empty:
                st.markdown("---")
                st.subheader(f"🗓️ {date_str}의 기록")
                st.write(f"🙏 **감사**: {target.iloc[0]['감사1']}, {target.iloc[0]['감사2']}, {target.iloc[0]['감사3']}")
                st.write(f"✨ **확언**: {target.iloc[0]['확언1']}, {target.iloc[0]['확언2']}, {target.iloc[0]['확언3']}")
                st.image(target.iloc[0]['이미지URL'])
