import streamlit as st


st.set_page_config(
    page_title="중기예보 지도 앱",
    page_icon="🗺️",
    layout="wide",
)

st.title("중기예보 지도 앱")
st.caption("Streamlit 프론트엔드 초기 스캐폴드")

st.info(
    "현재는 프로젝트 구조만 생성된 상태입니다. "
    "다음 단계에서 공공데이터포털 연동, 지도 시각화, API 연결을 구현하면 됩니다."
)
