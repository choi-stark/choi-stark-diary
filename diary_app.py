import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import google.generativeai as genai
import random
import time

# 1. 페이지 설정
st.set_page_config(page_title="미라클 다이어리", page_icon="✨", layout="wide")

# 2. 스타일 설정 (디자인 유지)
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .stButton>button { 
        width: 100%; border-radius: 15px; font-weight: bold; height: 3.5em; 
        background-color: #FFFFFF; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #E0E0E0;
    }
    .stButton>button:hover { transform: translateY(-2px); background-color: #F0F2F6; }
    /* AI 코멘트 박스 */
    .stSuccess, .stInfo { 
        border-radius: 15px; border-left: 8px solid #FF6B6B; 
        background-color: #FFFFFF; box-shadow: 0 2px 4px rgba(0,0,0,0.05); font-size: 1.1em;
    }
    /* 달력 커스텀 */
    .fc { background-color: white; padding: 20px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: none; }
    .fc-toolbar-title { font-size: 1.5em !important; color: #333; }
    .fc-event { cursor: pointer; border: none !important; background-color: transparent !important; }
    .fc-daygrid-event-dot { border: 4px solid #FF6B6B !important; border-radius: 50%; }
    </style>
    """, unsafe_allow_html=True)

# 3. 연결 및 AI 설정
conn = st.connection("gsheets", type=GSheetsConnection)

if "gemini_api_key" in st.secrets:
    genai.configure(api_key=st.secrets["gemini_api_key"])
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("Secrets 설정을 확인해주세요.")

# 데이터 로딩 (캐시 10분)
@st.cache_data(ttl=600)
def get_data():
    try:
        df = conn.read(worksheet="Sheet1")
        if df is not None and not df.empty:
            df['날짜'] = pd.to_datetime(df['날짜']).dt.strftime('%Y-%m-%d')
        return df
    except:
        return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "사진여부", "이미지URL", "의미"])

# AI 멘트 요청
def ask_gemini(prompt):
    try:
        response = model.generate_content(f"당신은 따뜻한 인생 멘토입니다. 2문장으로 답해주세요: {prompt}")
        return response.text
    except:
        return "당신의 긍정이 우주를 움직입니다."

# 세션 상태 초기화
if 'step' not in st.session_state: st.session_state.step = 1
if 'cal_key' not in st.session_state: st.session_state.cal_key = 100
if 'img_seed' not in st.session_state: st.session_state.img_seed = random.randint(1, 9999)
if 'img_meaning' not in st.session_state: st.session_state.img_meaning = "" # 이미지 의미 저장소

tab1, tab2 = st.tabs(["✍️ 오늘의 다이어리", "📅 지난 기록 모음"])

# ---------------- Tab 1: 오늘의 일기작성 ----------------
with tab1:
    # 1단계: 감사일기
    if st.session_state.step == 1:
        st.markdown("### 🌸 오늘 하루, 무엇이 감사했나요?")
        g1 = st.text_input("감사한 일 1", key="g1")
        g2 = st.text_input("감사한 일 2", key="g2")
        g3 = st.text_input("감사한 일 3", key="g3")
        
        if st.button("AI에게 감사 전송 ✨"):
            if g1 and g2 and g3:
                with st.spinner('제미나이가 감사를 읽고 있습니다...'):
                    st.session_state.g_comment = ask_gemini(f"감사내용: {g1}, {g2}, {g3}")
                    st.session_state.g_data = [g1, g2, g3]
                    st.session_state.step = 2
                    st.rerun()

    # 2단계: 확언일기
    elif st.session_state.step == 2:
        st.success(f"🤖 **Gemini's Insight**\n\n{st.session_state.g_comment}")
        
        st.markdown("### 🔥 내일의 나를 위한 확언")
        a1 = st.text_input("확언 1", key="a1")
        a2 = st.text_input("확언 2", key="a2")
        a3 = st.text_input("확언 3", key="a3")
        
        if st.button("확언 선포하기 🚀"):
            if a1 and a2 and a3:
                with st.spinner('확신을 우주에 새기는 중...'):
                    st.session_state.a_comment = ask_gemini(f"확언내용: {a1}, {a2}, {a3}")
                    st.session_state.a_data = [a1, a2, a3]
                    st.session_state.step = 3
                    st.rerun()

    # 3단계: 최종 확인 (이미지 해석 기능 복구됨)
    elif st.session_state.step == 3:
        st.success(f"💫 **Universal Response**\n\n{st.session_state.a_comment}")
        
        st.markdown("### 🖼️ 오늘의 에너지 이미지")
        img_url = f"https://picsum.photos/seed/{st.session_state.img_seed}/1200/600"
        st.image(img_url, use_container_width=True)
        
        # 🟢 [복구된 기능] 이미지 의미 해석 생성 및 표시
        if not st.session_state.img_meaning:
            with st.spinner("이미지의 메시지를 해석하는 중..."):
                st.session_state.img_meaning = ask_gemini(f"이 추상적인 이미지({img_url})가 본부장님의 확언과 어떤 연결고리가 있는지 희망적으로 해석해줘.")
        
        # 해석 텍스트 표시
        st.info(f"💡 **Image Message**: {st.session_state.img_meaning}")
        
        if st.button("🎉 다이어리 최종 완성 (저장)"):
            new_row = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes", "이미지URL": img_url, 
                "의미": st.session_state.img_meaning # 해석된 의미 저장
            }])
            try:
                # 저장 로직
                current_df = conn.read(worksheet="Sheet1", ttl=0)
                updated_df = pd.concat([current_df, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_df)
                
                # 풍선 대기
                st.balloons()
                time.sleep(2) 
                
                # 초기화
                st.cache_data.clear()
                st.session_state.step = 1
                st.session_state.cal_key += 1
                # 모든 세션 데이터 삭제
                for k in ['g_comment', 'a_comment', 'img_seed', 'g_data', 'a_data', 'img_meaning']:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()
            except Exception as e:
                st.error(f"저장 중 문제가 발생했습니다: {e}")

# ---------------- Tab 2: 지난 기록 ----------------
with tab2:
    st.markdown("### 📅 나의 미라클 여정")
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 새로고침"):
            st.cache_data.clear()
            st.session_state.cal_key += 1
            st.rerun()

    df = get_data()

    if not df.empty:
        # 달력 이벤트
        events = []
        for _, row in df.iterrows():
            events.append({
                "title": "", 
                "start": row["날짜"],
                "end": row["날짜"],
                "display": "list-item",
                "backgroundColor": "#FF6B6B",
                "borderColor": "#FF6B6B"
            })
        
        cal = calendar(
            events=events, 
            options={
                "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
                "initialView": "dayGridMonth",
                "height": 650,
                "navLinks": False, "selectable": True, "selectMirror": True, "dayMaxEvents": True
            },
            custom_css="""
                .fc-event-title { display: none; } 
                .fc-daygrid-event-dot { border-width: 5px; }
            """,
            key=f'miracle_cal_pretty_{st.session_state.cal_key}'
        )
        
        if cal.get("callback") == "dateClick":
            date_str = cal["dateClick"]["dateStr"]
            target = df[df["날짜"] == date_str]
            if not target.empty:
                st.divider()
                st.markdown(f"### 💌 {date_str}의 기록")
                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"**🙏 감사**\n\n1. {target.iloc[0]['감사1']}\n2. {target.iloc[0]['감사2']}\n3. {target.iloc[0]['감사3']}")
                with c2:
                    st.success(f"**🔥 확언**\n\n1. {target.iloc[0]['확언1']}\n2. {target.iloc[0]['확언2']}\n3. {target.iloc[0]['확언3']}")
                st.image(target.iloc[0]['이미지URL'], use_container_width=True)
                # 저장된 이미지 의미 표시
                if "의미" in target.columns:
                    st.warning(f"💡 **Image Message**: {target.iloc[0]['의미']}")
    else:
        st.info("아직 기록이 없습니다. 오늘부터 기적을 쌓아보세요!")
