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
    .fc-daygrid-event { border-radius: 50% !important; width: 14px !important; height: 14px !important; margin: 2px auto !important; background-color: #FF0000 !important; border: none !important; opacity: 1 !important; }
    .stButton>button { width: 100%; border-radius: 20px; font-weight: bold; height: 3.5em; }
    </style>
    """, unsafe_allow_html=True)

# 2. 연결 설정
conn = st.connection("gsheets", type=GSheetsConnection)

# 데이터 로딩 (캐시를 최소화하고 에러 발생 시 명확히 보고)
def get_data():
    try:
        # ttl=0으로 설정하여 매번 구글 시트에서 직접 가져옵니다.
        df = conn.read(worksheet="Sheet1", ttl=0)
        if df is not None and not df.empty:
            # 날짜 형식을 달력이 인식할 수 있는 문자열(YYYY-MM-DD)로 강제 변환
            df['날짜'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m-%d')
        return df
    except Exception as e:
        st.error(f"⚠️ 시트 읽기 실패: {e}")
        return pd.DataFrame()

# AI 설정
if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets 설정을 확인해주세요.")

# 세션 상태 초기화
if 'step' not in st.session_state: st.session_state.step = 1
if 'cal_key' not in st.session_state: st.session_state.cal_key = 0 # 달력 갱신용 키

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
                # 저장 직전 최신 데이터 로드 및 병합
                current_df = conn.read(worksheet="Sheet1", ttl=0)
                final_df = pd.concat([current_df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=final_df)
                
                st.balloons()
                st.session_state.step = 1
                st.session_state.cal_key += 1 # 달력 강제 갱신용 키 증가
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}")

# ---------------- Tab 2: 지난 기록 (점검 기능 추가) ----------------
with tab2:
    st.header("📅 지난 기록")
    
    # 데이터를 불러옵니다.
    df = get_data()

    # 🔍 [비서의 긴급 점검창] 데이터가 정말 들어왔는지 확인합니다.
    with st.expander("🛠️ 데이터 정상 로드 확인 (문제가 해결되면 닫으셔도 됩니다)"):
        if not df.empty:
            st.write("현재 시트에서 읽어온 최신 데이터 5건입니다:")
            st.table(df.tail(5)[["날짜", "감사1", "확언1"]])
        else:
            st.warning("현재 시트에서 읽어온 데이터가 전혀 없습니다. 구글 시트 자체를 확인해 보세요.")

    if st.button("🔄 달력 강제 새로고침"):
        st.session_state.cal_key += 1
        st.cache_data.clear()
        st.rerun()

    if not df.empty:
        # 달력 이벤트 생성
        events = []
        for _, row in df.iterrows():
            events.append({
                "title": "●",
                "start": row["날짜"],
                "end": row["날짜"],
                "display": "background",
                "color": "red"
            })
        
        # cal_key를 사용해 버튼을 누를 때마다 달력을 새로 그립니다.
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
