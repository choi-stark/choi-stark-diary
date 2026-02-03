import streamlit as st
from streamlit_gsheets import GSheetsConnection
from streamlit_calendar import calendar
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="GEVIS 다이어리", layout="wide")

# 1. 구글 스프레드시트 연결 (서비스 계정 자동 적용)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="Sheet1", ttl=0)
    st.sidebar.success("✅ 구글 시트 연결 성공!")
except Exception as e:
    st.sidebar.error("❌ 연결 확인 필요")
    st.sidebar.write(f"오류: {e}")
    df = pd.DataFrame(columns=["날짜", "제목", "내용", "작성시간"])

# --- CSS: 기록 있는 날 연한 초록색 동그라미 ---
st.markdown("""
    <style>
    .fc-daygrid-event {
        background-color: rgba(144, 238, 144, 0.7) !important;
        border-radius: 50% !important;
        width: 24px !important; height: 24px !important;
        margin: 0 auto !important; margin-top: -22px !important;
        z-index: 0 !important;
    }
    .fc-event-main { display: none !important; }
    .fc-daygrid-day-number { position: relative !important; z-index: 1 !important; }
    </style>
    """, unsafe_allow_html=True)

menu = st.sidebar.selectbox("메뉴", ["일기 쓰기", "지난 기록 보기"])

if menu == "일기 쓰기":
    st.title("📝 오늘을 기록하세요")
    with st.form("diary_form", clear_on_submit=True):
        date = st.date_input("날짜", datetime.now())
        title = st.text_input("제목")
        content = st.text_area("내용", height=200)
        submit = st.form_submit_button("구글 시트에 저장")

        if submit and title and content:
            new_row = pd.DataFrame([{
                "날짜": date.strftime("%Y-%m-%d"),
                "제목": title,
                "내용": content,
                "작성시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            conn.update(worksheet="Sheet1", data=updated_df)
            st.success("🎉 데이터베이스에 안전하게 보관되었습니다!")
            st.balloons()
            st.rerun()

elif menu == "지난 기록 보기":
    st.title("📅 나의 활동 달력")
    if not df.empty:
        df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce').dt.strftime('%Y-%m-%d')
        recorded_dates = df['날짜'].dropna().unique()
        events = [{"start": d, "end": d, "display": "block"} for d in recorded_dates]
        calendar(events=events, options={"initialView": "dayGridMonth"})
        st.divider()
        st.dataframe(df.sort_values("날짜", ascending=False), use_container_width=True)
    else:
        st.info("기록된 데이터가 없습니다.")