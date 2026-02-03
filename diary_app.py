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

# 2. 시스템 상태 점검 및 연결
st.sidebar.title("🚀 시스템 상태")
conn = st.connection("gsheets", type=GSheetsConnection)

# AI 설정 (모델명 오류 해결: gemini-1.5-flash 사용)
if "gemini_api_key" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["gemini_api_key"])
        # 가장 안정적인 모델 호출 방식으로 변경
        model = genai.GenerativeModel('gemini-1.5-flash')
        st.sidebar.success("✅ AI 엔진 준비 완료")
    except Exception as e:
        st.sidebar.error(f"❌ AI 연결 실패: {e}")
else:
    st.sidebar.error("❌ API 키를 찾을 수 없음")

# 데이터 로드 함수 (오류 보고 기능 추가)
def get_data():
    try:
        # 캐시를 무시하고 항상 최신 데이터를 읽어옵니다.
        data = conn.read(worksheet="Sheet1", ttl=0)
        st.sidebar.success(f"✅ 시트 연결 성공 (기록: {len(data)}건)")
        return data
    except Exception as e:
        st.sidebar.error(f"❌ 시트 읽기 실패: {e}")
        return pd.DataFrame(columns=["날짜", "감사1", "감사2", "감사3", "확언1", "확언2", "확언3", "사진여부", "이미지URL", "의미"])

df = get_data()

# AI 답변 생성 (에러 시 대체 문구 보장)
def ask_gemini(prompt):
    try:
        # 모델 응답 대기 시간을 고려하여 타임아웃 방지
        response = model.generate_content(f"당신은 최본부장님의 단호한 멘토입니다. 2문장으로 결의를 다져주세요: {prompt}")
        return response.text
    except Exception as e:
        st.sidebar.warning(f"⚠️ AI 응답 지연: {e}")
        return "당신의 의지가 곧 현실입니다. 흔들리지 말고 전진하십시오."

# 3. 세션 상태 관리 (기억 상실 방지)
if 'step' not in st.session_state: st.session_state.step = 1
if 'img_seed' not in st.session_state: st.session_state.img_seed = random.randint(1, 9999)
if 'g_comment' not in st.session_state: st.session_state.g_comment = ""
if 'a_comment' not in st.session_state: st.session_state.a_comment = ""

tab1, tab2 = st.tabs(["오늘의 일기작성", "지난 기록"])

# ---------------- Tab 1: 오늘의 일기작성 ----------------
with tab1:
    if st.session_state.step == 1:
        st.header("🙏 1단계: 감사일기")
        g1 = st.text_input("감사 1", key="g1_input")
        g2 = st.text_input("감사 2", key="g2_input")
        g3 = st.text_input("감사 3", key="g3_input")
        if st.button("제출 및 AI 코멘트 듣기"):
            if g1 and g2 and g3:
                with st.spinner('제미나이가 본부장님의 감사를 읽고 있습니다...'):
                    st.session_state.g_comment = ask_gemini(f"감사 내용: {g1}, {g2}, {g3}")
                    st.session_state.g_data = [g1, g2, g3]
                    st.session_state.step = 2
                    st.rerun()

    elif st.session_state.step == 2:
        # 🎯 AI 코멘트가 반드시 보이도록 상단에 배치
        st.success(f"🤖 **제미나이의 멘토링**\n\n{st.session_state.g_comment}")
        
        st.header("✨ 2단계: 확언일기")
        a1 = st.text_input("확언 1", key="a1_input")
        a2 = st.text_input("확언 2", key="a2_input")
        a3 = st.text_input("확언 3", key="a3_input")
        if st.button("제출 및 확신 멘트 듣기"):
            if a1 and a2 and a3:
                with st.spinner('우주의 확신을 가져오는 중...'):
                    st.session_state.a_comment = ask_gemini(f"확언 내용: {a1}, {a2}, {a3}")
                    st.session_state.a_data = [a1, a2, a3]
                    st.session_state.step = 3
                    st.rerun()

    elif st.session_state.step == 3:
        st.info(f"💫 **오늘의 확신**\n\n{st.session_state.a_comment}")
        img_url = f"https://picsum.photos/seed/{st.session_state.img_seed}/1200/600"
        st.image(img_url, use_container_width=True)
        
        if 'img_meaning' not in st.session_state:
            st.session_state.img_meaning = ask_gemini(f"이미지({img_url})와 본부장님의 결의의 관계")
        st.write(f"💡 이미지의 의미: {st.session_state.img_meaning}")
        
        if st.button("🔥 오늘의 결의 최종 기록"):
            new_row = pd.DataFrame([{
                "날짜": datetime.now().strftime('%Y-%m-%d'),
                "감사1": st.session_state.g_data[0], "감사2": st.session_state.g_data[1], "감사3": st.session_state.g_data[2],
                "확언1": st.session_state.a_data[0], "확언2": st.session_state.a_data[1], "확언3": st.session_state.a_data[2],
                "사진여부": "Yes", "이미지URL": img_url, "의미": st.session_state.img_meaning
            }])
            try:
                # 저장 직전 데이터를 동기화합니다.
                current_all = conn.read(worksheet="Sheet1", ttl=0)
                updated_all = pd.concat([current_all, new_row], ignore_index=True)
                conn.update(worksheet="Sheet1", data=updated_all)
                
                st.balloons()
                time.sleep(1) # 구글 서버 반영 시간을 위해 1초 대기
                st.cache_data.clear()
                st.session_state.step = 1
                for key in ['g_comment', 'a_comment', 'img_meaning', 'img_seed']:
                    if key in st.session_state: del st.session_state[key]
                st.rerun()
            except Exception as e:
                st.error(f"저장 실패: {e}. 시트 공유 설정을 확인하세요.")

# ---------------- Tab 2: 지난 기록 (달력) ----------------
with tab2:
    st.header("📅 지난 기록")
    if st.button("🔄 실시간 동기화 (기록이 안 보일 때 클릭)"):
        st.cache_data.clear()
        st.rerun()

    if df.empty or len(df) == 0:
        st.warning("현재 시트에 기록된 데이터가 없습니다. 오늘 첫 일기를 끝까지 제출해 보세요!")
    else:
        # 달력에 빨간 점 찍기
        events = [{"title": "●", "start": str(row["날짜"]), "end": str(row["날짜"]), "display": "background", "color": "red"} for _, row in df.iterrows()]
        
        cal = calendar(events=events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}, "initialView": "dayGridMonth", "height": 700}, key='miracle_cal_final_fixed')
        
        if cal.get("callback") == "dateClick":
            date_click = cal["dateClick"]["dateStr"]
            target = df[df["날짜"] == date_click]
            if not target.empty:
                st.markdown("---")
                st.subheader(f"🗓️ {date_click}의 기록")
                st.write(f"🙏 **감사**: {target.iloc[0]['감사1']}, {target.iloc[0]['감사2']}, {target.iloc[0]['감사3']}")
                st.write(f"✨ **확언**: {target.iloc[0]['확언1']}, {target.iloc[0]['확언2']}, {target.iloc[0]['확언3']}")
                st.image(target.iloc[0]['이미지URL'])
