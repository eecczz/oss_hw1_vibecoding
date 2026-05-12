# Public Toilet Map App

## 프로젝트 개요

공중화장실 위치 데이터를 활용해 지도 기반 조회와 CRUD API를 제공하는 `uv` workspace 기반 프로젝트입니다. FastAPI 백엔드, Streamlit 프론트엔드, SQLite DB를 함께 사용합니다.

## 주요 기능

- CSV 데이터를 SQLite DB로 자동 적재
- JWT 기반 회원가입과 로그인
- 인증 사용자 기준 공중화장실 CRUD API
- 위치 기반 근처 화장실 검색
- Streamlit 기반 지도 시각화
- Docker Compose 실행 환경 제공

## 기술 스택

- Backend: FastAPI, Python
- Frontend: Streamlit
- Database: SQLite
- Auth: JWT
- Tooling: uv, Docker Compose

## 로컬 실행

```bash
uv sync --all-packages
uv run --package backend uvicorn app.main:app --reload
uv run --package frontend streamlit run app.py
```

## Docker 실행

```bash
docker compose up --build
```

- FastAPI: `http://localhost:8000`
- Streamlit: `http://localhost:8501`

## 주요 API

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/toilets`
- `GET /api/v1/toilets/map`
- `GET /api/v1/toilets/nearby`
- `POST /api/v1/toilets`
- `PUT /api/v1/toilets/{management_number}`
- `DELETE /api/v1/toilets/{management_number}`
