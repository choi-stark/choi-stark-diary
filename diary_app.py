import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import google.generativeai as genai
import random
import time

# 1. 페이지 설정
st.set_page_config(page_title="미라클 다이어리", layout="wide")

# 2. 시스템 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 로딩 함수 (서버 보호를 위해 15분간 데이터를 기억합니다)
@st.cache_data(ttl=900)
def get_data():
    try:
        # worksheet 이름을 "Sheet1"으로 고정하여 읽어옵니다.
        df = conn.read(worksheet="Sheet1")
        if df is not None and not df.empty:
            df['날짜'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m-%d')
        return df
    except Exception as e:
        if "429" in str(e):
            st.error("⚠️ 구글 서버가 과부하로 인해 잠시 문을 닫았습니다. 2분만 기다려 주세요.")
        return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "사진여부", "이미지URL", "의미"])

# AI 설정
if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets 설정을 확인해주세요.")

# 세션 상태 초기화
if 'step' not in st.session_state: st.session_state.step = 1
if 'cal_key' not in st.session_state: st.session_state.cal_key = 0

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
                st.session_state.g_data = [g1, g2, g3]
                st.session_state.step = 2
                st.rerun()

    elif st.session_state.step == 2:
        st.header("✨ 2단계: 확언일기 작성")
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
        img_url = f"https://picsum.photos/seed/{random.randint(1,9999)}/1200/600"
        st.image(img_url, use_container_width=True)
        
        if st.button("🔥 최종 기록 제출"):
            new_row = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes", "이미지URL": img_url, "의미": "오늘의 결의"
            }])
            try:
                # 저장 시에만 캐시를 지우고 서버와 통신합니다.
                current_df = conn.read(worksheet="Sheet1", ttl=0)
                final_df = pd.concat([current_df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=final_df)
                
                # 모든 단계가 성공했을 때만 풍선을 띄우고 초기화합니다.
                st.balloons()
                st.cache_data.clear()
                st.session_state.step = 1
                st.session_state.cal_key += 1
                st.rerun()
            except Exception as e:
                st.error(f"⚠️ 구글 서버 차단 상태입니다. 1~2분 뒤에 다시 버튼을 눌러주세요. ({e})")

# ---------------- Tab 2: 지난 기록 (복구 보장) ----------------
with tab2:
    st.header("📅 지난 기록")
    
    # 데이터를 불러옵니다.
    df = get_data()

    if st.button("🔄 최신 기록으로 동기화 (차단 해제용)"):
        st.cache_data.clear()
        st.session_state.cal_key += 1
        st.rerun()

    if not df.empty and len(df) > 0:
        events = [{"title": "●", "start": row["날짜"], "end": row["날짜"], "display": "background", "color": "red"} for _, row in df.iterrows()]
        
        # 고유한 key를 부여해 달력을 강제로 새로 고침합니다.
        cal = calendar(
            events=events, 
            options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "initialView": "dayGridMonth", "height": 700}, 
            key=f'miracle_cal_{st.session_state.cal_key}'
        )
        
        if cal.get("callback") == "dateClick":
            date_str = cal["dateClick"]["dateStr"]
            target = df[df["날짜"] == date_str]
            if not target.empty:
                st.markdown("---")
                st.subheader(f"🗓️ {date_str}의 기록")
                st.write(f"🙏 **감사**: {target.iloc[0]['감사1']}, {target.iloc[0]['감사2']}, {target.iloc[0]['감사3']}")
                st.write(f"✨ **확언**: {target.iloc[0]['확언1']}, {target.iloc[0]['확언2']}, {target.iloc[0]['확언3']}")
                st.image(target.iloc[0]['이미지URL'])
    else:
        st.info("아직 기록된 일기가 없습니다. 오늘 첫 기록을 제출해 보세요!")
