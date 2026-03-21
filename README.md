# Weather Map App Scaffold

`uv` workspace 기반으로 `Streamlit + FastAPI + SQLite3` 프로젝트 구조를 초기화한 상태입니다.

## Structure

```text
.
├─ frontend/
│  ├─ app.py
│  └─ pyproject.toml
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ db/
│  │  ├─ __init__.py
│  │  ├─ main.py
│  │  └─ settings.py
│  ├─ data/
│  └─ pyproject.toml
├─ .python-version
└─ pyproject.toml
```

## Usage

1. `uv` 설치
2. 루트에서 의존성 설치

```bash
uv sync --all-packages
```

3. 백엔드 실행

```bash
uv run --package backend uvicorn app.main:app --reload
```

4. 프론트엔드 실행

```bash
uv run --package frontend streamlit run app.py
```

## Notes

- 현재는 기능 구현 전 단계이므로 최소 실행 구조만 포함합니다.
- SQLite 파일은 `backend/data/app.db` 경로를 기본값으로 사용합니다.
