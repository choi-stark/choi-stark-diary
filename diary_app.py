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

# 2. 연결 및 AI 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# AI 엔진 설정 (안정적인 호출 방식)
if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets 설정을 확인해주세요.")

# 데이터 로딩 (서버 과부하 방지를 위해 10분간 캐시)
@st.cache_data(ttl=600)
def get_data():
    try:
        df = conn.read(worksheet="Sheet1")
        if df is not None and not df.empty:
            df['날짜'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m-%d')
        return df
    except Exception as e:
        if "429" in str(e):
            st.error("⚠️ 구글 서버가 과부하로 차단 중입니다. 5분만 창을 닫고 기다려주세요.")
        else:
            st.error(f"❌ 데이터 읽기 오류: {e}")
        return pd.DataFrame()

# 3. 세션 상태 관리
if 'step' not in st.session_state: st.session_state.step = 1
if 'cal_key' not in st.session_state: st.session_state.cal_key = 100

tab1, tab2 = st.tabs(["오늘의 일기작성", "지난 기록"])

# ---------------- Tab 1: 오늘의 일기작성 ----------------
with tab1:
    if st.session_state.step == 1:
        st.header("🙏 1단계: 감사일기")
        g1 = st.text_input("감사 1", key="g1_v2")
        g2 = st.text_input("감사 2", key="g2_v2")
        g3 = st.text_input("감사 3", key="g3_v2")
        if st.button("제출"):
            if g1 and g2 and g3:
                st.session_state.g_data = [g1, g2, g3]
                st.session_state.step = 2
                st.rerun()

    elif st.session_state.step == 2:
        st.header("✨ 2단계: 확언일기")
        a1 = st.text_input("확언 1", key="a1_v2")
        a2 = st.text_input("확언 2", key="a2_v2")
        a3 = st.text_input("확언 3", key="a3_v2")
        if st.button("제출 "):
            if a1 and a2 and a3:
                st.session_state.a_data = [a1, a2, a3]
                st.session_state.step = 3
                st.rerun()

    elif st.session_state.step == 3:
        st.header("🎁 최종 확인")
        img_url = f"https://picsum.photos/seed/{random.randint(1,9999)}/1200/600"
        st.image(img_url, use_container_width=True)
        
        if st.button("🔥 오늘의 결의 최종 기록 제출"):
            new_row = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes", "이미지URL": img_url, "의미": "성공적인 하루"
            }])
            try:
                # 🎯 [핵심] 저장 시에는 실시간 데이터를 강제로 읽어와서 합칩니다.
                with st.spinner('구글 시트에 기록 중... 잠시만 기다려 주세요.'):
                    current_df = conn.read(worksheet="Sheet1", ttl=0)
                    updated_df = pd.concat([current_df, new_row], ignore_index=True)
                    conn.update(worksheet="Sheet1", data=updated_df)
                    
                    # 모든 과정이 끝나야 풍선이 뜹니다.
                    st.success("✅ 우주에 본부장님의 결의가 기록되었습니다!")
                    st.balloons()
                    time.sleep(2) # 풍선을 볼 시간을 줍니다.
                    
                    st.cache_data.clear()
                    st.session_state.step = 1
                    st.session_state.cal_key += 1
                    st.rerun()
            except Exception as e:
                st.error(f"저장 실패! 구글 서버가 응답하지 않습니다: {e}")

# ---------------- Tab 2: 지난 기록 (복구 시스템) ----------------
with tab2:
    st.header("📅 지난 기록")
    
    # 데이터를 불러옵니다.
    df = get_data()

    if st.button("🔄 기록 강제 동기화 (기록 제출 후 클릭)"):
        st.cache_data.clear()
        st.session_state.cal_key += 1
        st.rerun()

    if not df.empty:
        # 달력 점 찍기
        events = [{"title": "●", "start": r["날짜"], "end": r["날짜"], "display": "background", "color": "red"} for _, r in df.iterrows()]
        
        calendar(
            events=events, 
            options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "initialView": "dayGridMonth", "height": 700}, 
            key=f'miracle_cal_{st.session_state.cal_key}'
        )
        
        # 🔍 데이터가 실제 있는지 표로 보여줍니다.
        with st.expander("📝 현재 시트 데이터 직접 확인"):
            st.table(df.tail(5)[["날짜", "감사1", "확언1"]])
    else:
        st.info("아직 기록이 없습니다. 일기를 제출하고 '동기화'를 눌러보세요.")
