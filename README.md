# Public Toilet Map App

`uv` workspace 기반의 `Streamlit + FastAPI + SQLite3` 공중화장실 지도 앱입니다.

## Features

- `backend/data/data.csv`를 SQLite DB로 자동 적재
- 제약조건이 명시된 정규화 테이블 설계
- JWT 기반 회원가입, 로그인, 사용자 인증
- 인증 후 접근 가능한 공중화장실 CRUD 및 근처 검색 API
- Streamlit 메인 페이지 지도 시각화
- glassmorphism 스타일 UI와 위치 기반 강조 지도

## Local Run

```bash
uv sync --all-packages
uv run --package backend uvicorn app.main:app --reload
uv run --package frontend streamlit run app.py
```

## Docker Run

`.env`에 최소한 `JWT_SECRET_KEY`를 추가한 뒤 실행합니다.

```bash
docker compose up --build
```

- FastAPI: `http://localhost:8000`
- Streamlit: `http://localhost:8501`

백엔드 SQLite DB는 `backend-data` named volume에 유지되고, CSV 원본은 이미지에 포함된 [backend/data/data.csv](C:/Users/swh06/Documents/oss_hw1/backend/data/data.csv)를 사용합니다.

## Main API

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /health`
- `POST /api/v1/toilets/import`
- `GET /api/v1/toilets`
- `GET /api/v1/toilets/map`
- `GET /api/v1/toilets/nearby`
- `GET /api/v1/toilets/{management_number}`
- `POST /api/v1/toilets`
- `PUT /api/v1/toilets/{management_number}`
- `DELETE /api/v1/toilets/{management_number}`
