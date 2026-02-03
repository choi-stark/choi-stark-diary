import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="최본부장님의 감사 & 확언 일기", layout="centered")

st.title("✍️ 오늘의 감사 & 확언 일기")
st.write(f"날짜: {datetime.now().strftime('%Y-%m-%d')}")

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 1. 감사 일기 섹션
st.header("🙏 감사 일기 (3가지)")
g1 = st.text_input("1. 첫 번째 감사한 일")
g2 = st.text_input("2. 두 번째 감사한 일")
g3 = st.text_input("3. 세 번째 감사한 일")

if g1 or g2 or g3:
    st.info("💡 제비스의 코멘트: 작은 감사함이 모여 본부장님의 하루를 더 풍요롭게 만들 거예요!")

# 2. 확언 일기 섹션
st.header("✨ 확언 일기 (3가지)")
a1 = st.text_input("1. 첫 번째 확언")
a2 = st.text_input("2. 두 번째 확언")
a3 = st.text_input("3. 세 번째 확언")

if a1 or a2 or a3:
    st.success("💡 제비스의 코멘트: 본부장님은 이미 말씀하신 대로 되어가고 계십니다. 응원합니다!")

# 3. 사진 업로드
st.header("📸 오늘의 사진")
uploaded_file = st.file_uploader("오늘을 기억할 사진 한 장을 올려주세요", type=['png', 'jpg', 'jpeg'])
if uploaded_file:
    st.image(uploaded_file, caption="업로드된 사진", use_container_width=True)

# 4. 저장 버튼
if st.button("오늘의 일기 저장하기"):
    if not (g1 and g2 and g3 and a1 and a2 and a3):
        st.warning("모든 항목을 작성해 주세요!")
    else:
        # 데이터 정리
        new_data = pd.DataFrame([{
            "날짜": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "감사1": g1, "감사2": g2, "감사3": g3,
            "확언1": a1, "확언2": a2, "확언3": a3,
            "사진여부": "Yes" if uploaded_file else "No"
        }])
        
        # 기존 데이터 읽기 및 추가
        existing_data = conn.read(worksheet="Sheet1")
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        
        # 시트에 저장
        conn.update(worksheet="Sheet1", data=updated_df)
        st.balloons()
        st.success("시트에 성공적으로 기록되었습니다! 수고하셨습니다, 본부장님.")
