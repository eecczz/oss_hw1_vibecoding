from __future__ import annotations

import math
import os
from typing import Any

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
from dotenv import load_dotenv
from streamlit_geolocation import streamlit_geolocation


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")
DEFAULT_CENTER = {"latitude": 36.35, "longitude": 127.8, "zoom": 6.6}
MIN_ICON_SIZE = 18
MAX_ICON_SIZE = 54
DEFAULT_ICON_SIZE = 24
TOILET_ICON_TEXT = "\uf7bd"


st.set_page_config(page_title="공중화장실 지도", page_icon="🚻", layout="wide")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap');
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.2/css/all.min.css');

        :root {
            --bg: #f7f6f2;
            --surface: rgba(255, 255, 255, 0.82);
            --surface-strong: rgba(255, 255, 255, 0.92);
            --text: #2f343b;
            --muted: #6f7477;
            --green: #38a84a;
            --green-soft: #edf7ee;
            --orange: #e86d3b;
            --line: rgba(57, 63, 69, 0.12);
        }

        html, body, [class*="css"] {
            font-family: 'Noto Sans KR', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(56, 168, 74, 0.08), transparent 24%),
                radial-gradient(circle at 85% 18%, rgba(232, 109, 59, 0.08), transparent 18%),
                linear-gradient(180deg, #fcfcfa 0%, var(--bg) 100%);
            color: var(--text);
        }

        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }

        .glass-card {
            background: var(--surface);
            border: 1px solid var(--line);
            box-shadow: 0 18px 40px rgba(42, 48, 55, 0.08);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border-radius: 22px;
            padding: 1.25rem 1.4rem;
        }

        .hero-card {
            padding: 1.8rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(245, 248, 242, 0.9));
        }

        .hero-title {
            font-size: 2.35rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
            letter-spacing: -0.03em;
            color: var(--text);
        }

        .hero-subtitle {
            color: var(--muted);
            font-size: 1rem;
        }

        .stat-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
            margin-top: 1.1rem;
        }

        .stat-pill {
            background: var(--surface-strong);
            border: 1px solid rgba(56, 168, 74, 0.14);
            border-radius: 20px;
            padding: 0.9rem 1rem;
        }

        .stat-label {
            font-size: 0.82rem;
            color: var(--muted);
        }

        .stat-value {
            font-size: 1.3rem;
            font-weight: 700;
            margin-top: 0.15rem;
            color: var(--green);
        }

        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
            color: var(--text);
        }

        div[data-testid="stMetric"] {
            background: var(--surface-strong);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 0.7rem 0.9rem;
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted);
        }

        div[data-testid="stMetricValue"] {
            color: var(--text);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.74);
            border-radius: 14px;
            color: var(--text);
            padding: 0.55rem 1rem;
            border: 1px solid var(--line);
        }

        .stTabs [aria-selected="true"] {
            background: var(--green-soft) !important;
            color: var(--green) !important;
            border-color: rgba(56, 168, 74, 0.35) !important;
        }

        .stButton > button, .stFormSubmitButton > button {
            background: linear-gradient(135deg, var(--green), #47b55b);
            color: white;
            border: none;
            border-radius: 999px;
            font-weight: 700;
            box-shadow: 0 10px 20px rgba(56, 168, 74, 0.2);
        }

        .stButton > button:hover, .stFormSubmitButton > button:hover {
            background: linear-gradient(135deg, #319442, #3da950);
            color: white;
        }

        .stTextInput input {
            background: rgba(255, 255, 255, 0.88);
            color: var(--text);
            border-radius: 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_session() -> None:
    st.session_state.setdefault("access_token", None)
    st.session_state.setdefault("current_user", None)
    st.session_state.setdefault("request_location", False)


def api_request(
    method: str,
    path: str,
    *,
    token: str | None = None,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> Any:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    response = requests.request(
        method=method,
        url=f"{BACKEND_API_URL}{path}",
        headers=headers,
        params=params,
        json=json,
        timeout=30,
    )
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        raise RuntimeError(str(detail))
    if response.content:
        return response.json()
    return None


def fetch_authenticated_markers(token: str) -> list[dict[str, Any]]:
    return api_request("GET", "/api/v1/toilets/map", token=token)


def login(email: str, password: str) -> None:
    payload = api_request(
        "POST",
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    st.session_state.access_token = payload["access_token"]
    st.session_state.current_user = payload["user"]


def register(name: str, email: str, password: str) -> None:
    payload = api_request(
        "POST",
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": password},
    )
    st.session_state.access_token = payload["access_token"]
    st.session_state.current_user = payload["user"]


def sync_current_user() -> None:
    token = st.session_state.access_token
    if not token:
        return
    try:
        st.session_state.current_user = api_request(
            "GET",
            "/api/v1/auth/me",
            token=token,
        )
    except Exception:
        st.session_state.access_token = None
        st.session_state.current_user = None


def logout() -> None:
    st.session_state.access_token = None
    st.session_state.current_user = None
    st.session_state.request_location = False


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    return 2 * radius * math.asin(math.sqrt(a))


def apply_distance_scaling(
    markers: list[dict[str, Any]],
    current_location: dict[str, float] | None,
) -> list[dict[str, Any]]:
    prepared = [dict(marker) for marker in markers]
    if not current_location:
        for marker in prepared:
            marker["icon_size"] = DEFAULT_ICON_SIZE
            marker["distance_meters"] = None
            marker["icon_text"] = TOILET_ICON_TEXT
        return prepared

    for marker in prepared:
        marker["distance_meters"] = haversine_distance(
            current_location["latitude"],
            current_location["longitude"],
            float(marker["latitude"]),
            float(marker["longitude"]),
        )

    max_distance = max(marker["distance_meters"] for marker in prepared) if prepared else 1.0
    max_distance = max(max_distance, 1.0)

    for marker in prepared:
        normalized = min(marker["distance_meters"] / max_distance, 1.0)
        inverse_weight = 1.0 - normalized
        scaled = MIN_ICON_SIZE + (MAX_ICON_SIZE - MIN_ICON_SIZE) * (inverse_weight**0.35)
        marker["icon_size"] = int(round(max(MIN_ICON_SIZE, min(MAX_ICON_SIZE, scaled))))
        marker["icon_text"] = TOILET_ICON_TEXT

    return prepared


def format_marker_frame(markers: list[dict[str, Any]]) -> pd.DataFrame:
    frame = pd.DataFrame(markers)
    if frame.empty:
        return frame

    distance_series = (
        frame["distance_meters"]
        if "distance_meters" in frame.columns
        else pd.Series([None] * len(frame))
    )
    frame["distance_text"] = distance_series.apply(
        lambda value: f"거리: {value:,.0f}m" if pd.notna(value) else "거리 정보 없음"
    )
    frame["latitude_text"] = frame["latitude"].apply(lambda value: f"{value:.5f}")
    frame["longitude_text"] = frame["longitude"].apply(lambda value: f"{value:.5f}")
    frame["display_address"] = frame["road_address"].fillna(frame["lot_address"]).fillna("-")
    frame["emergency_bell_flag"] = frame["emergency_bell_flag"].map({True: "Y", False: "N"})
    frame["entrance_cctv_flag"] = frame["entrance_cctv_flag"].map({True: "Y", False: "N"})
    frame["diaper_changing_table_flag"] = frame["diaper_changing_table_flag"].map(
        {True: "Y", False: "N"}
    )
    return frame


def make_tooltip() -> dict[str, str]:
    return {
        "html": """
        <div style="font-size: 13px; min-width: 250px;">
            <div><b>{name}</b></div>
            <div>구분: {toilet_type_name}</div>
            <div>주소: {display_address}</div>
            <div>위도: {latitude_text}</div>
            <div>경도: {longitude_text}</div>
            <div>비상벨: {emergency_bell_flag}</div>
            <div>CCTV: {entrance_cctv_flag}</div>
            <div>기저귀교환대: {diaper_changing_table_flag}</div>
            <div>{distance_text}</div>
        </div>
        """,
        "style": {"backgroundColor": "#ffffff", "color": "#2f343b"},
    }


def build_map(markers: list[dict[str, Any]], current_location: dict[str, float] | None) -> pdk.Deck:
    frame = format_marker_frame(markers)
    layers: list[pdk.Layer] = []

    if not frame.empty:
        layers.append(
            pdk.Layer(
                "TextLayer",
                data=frame,
                get_position=["longitude", "latitude"],
                get_text="icon_text",
                get_size="icon_size",
                size_units="pixels",
                get_color=[47, 52, 59, 235],
                get_text_anchor="middle",
                get_alignment_baseline="center",
                font_family="Font Awesome 6 Free",
                font_weight=900,
                pickable=True,
            )
        )

    if current_location:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=[current_location],
                get_position=["longitude", "latitude"],
                get_fill_color=[56, 168, 74, 235],
                get_line_color=[255, 255, 255, 220],
                line_width_min_pixels=2,
                stroked=True,
                get_radius=95,
                radius_units="meters",
                pickable=True,
            )
        )

    view_state = (
        pdk.ViewState(
            latitude=current_location["latitude"],
            longitude=current_location["longitude"],
            zoom=13,
            pitch=25,
        )
        if current_location
        else pdk.ViewState(**DEFAULT_CENTER, pitch=20)
    )

    return pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_provider="carto",
        map_style="light_no_labels",
        tooltip=make_tooltip(),
    )


def render_auth_screen() -> None:
    left, right = st.columns([1.15, 1], vertical_alignment="center")
    with left:
        st.markdown(
            """
            <div class="glass-card hero-card">
                <div class="hero-title">Public Toilet Navigator</div>
                <div class="hero-subtitle">
                    로그인 후 전국 공중화장실 위치를 지도에서 바로 확인하고, 현재 위치 기준으로 아이콘 크기를 조절할 수 있습니다.
                </div>
                <div class="stat-strip">
                    <div class="stat-pill">
                        <div class="stat-label">보안 인증</div>
                        <div class="stat-value">JWT</div>
                    </div>
                    <div class="stat-pill">
                        <div class="stat-label">지도 인터페이스</div>
                        <div class="stat-value">Public UI</div>
                    </div>
                    <div class="stat-pill">
                        <div class="stat-label">데이터 소스</div>
                        <div class="stat-value">SQLite</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        tabs = st.tabs(["로그인", "회원가입"])
        with tabs[0]:
            with st.form("login_form", border=False):
                email = st.text_input("이메일", placeholder="you@example.com")
                password = st.text_input("비밀번호", type="password", placeholder="8자 이상")
                submitted = st.form_submit_button("로그인", use_container_width=True)
                if submitted:
                    try:
                        login(email, password)
                        st.rerun()
                    except Exception as error:
                        st.error(str(error))
        with tabs[1]:
            with st.form("register_form", border=False):
                name = st.text_input("이름", placeholder="홍길동")
                email = st.text_input("가입 이메일", placeholder="you@example.com")
                password = st.text_input("가입 비밀번호", type="password", placeholder="8자 이상")
                submitted = st.form_submit_button("회원가입", use_container_width=True)
                if submitted:
                    try:
                        register(name, email, password)
                        st.rerun()
                    except Exception as error:
                        st.error(str(error))
        st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard() -> None:
    token = st.session_state.access_token
    user = st.session_state.current_user or {}

    top_left, top_right = st.columns([5, 1], vertical_alignment="center")
    with top_left:
        st.markdown(
            f"""
            <div class="glass-card hero-card">
                <div class="hero-title">공중화장실 지도</div>
                <div class="hero-subtitle">
                    {user.get("name", "")}님으로 로그인되어 있습니다. 마우스를 올리면 화장실 상세 정보를 볼 수 있습니다.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_right:
        st.markdown('<div class="glass-card" style="padding: 1rem;">', unsafe_allow_html=True)
        st.write(f"**{user.get('name', '')}**")
        st.caption(user.get("email", ""))
        if st.button("로그아웃", use_container_width=True):
            logout()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    all_markers = fetch_authenticated_markers(token)
    current_location: dict[str, float] | None = None

    map_col, side_col = st.columns([3.25, 1.1], vertical_alignment="top")
    with side_col:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">요약 정보</div>', unsafe_allow_html=True)

        if st.button("현재 위치 기준 크기 조절", use_container_width=True):
            st.session_state.request_location = True

        location = streamlit_geolocation() if st.session_state.request_location else None
        if location and location.get("latitude") and location.get("longitude"):
            current_location = {
                "latitude": float(location["latitude"]),
                "longitude": float(location["longitude"]),
            }

        display_markers = apply_distance_scaling(all_markers, current_location)
        nearest_distance = min(
            (
                marker["distance_meters"]
                for marker in display_markers
                if marker["distance_meters"] is not None
            ),
            default=None,
        )

        st.metric("전체 화장실", f"{len(display_markers):,}")
        st.metric(
            "가장 가까운 거리",
            f"{nearest_distance:.0f}m" if nearest_distance is not None else "위치 대기",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    display_markers = apply_distance_scaling(all_markers, current_location)
    with map_col:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.pydeck_chart(build_map(display_markers, current_location), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


inject_styles()
init_session()
sync_current_user()

if st.session_state.access_token:
    try:
        render_dashboard()
    except Exception as error:
        st.error(str(error))
else:
    render_auth_screen()
