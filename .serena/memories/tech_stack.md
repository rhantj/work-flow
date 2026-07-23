# 기술 스택

버전 원본은 `convention/` 3개 파일(ai.md, backend.md, frontend.md). 충돌 시 그쪽이 기준.

## Frontend (`App/frontend`)
- React 19.2 + Vite + TypeScript. 라우팅 `react-router` 7.
- UI: Radix UI + MUI 7 혼용, Tailwind(`tailwind-merge`, `tw-animate-css`), lucide 아이콘.
- 차트 recharts, 폼 react-hook-form, 토스트 sonner, DnD react-dnd.
- 테스트: vitest (`npm test` → `vitest run`).
- 빌드 시 주입되는 플래그: `VITE_ENABLE_DEMO_AUTH` (compose build args, 기본 true).
  로그인 화면의 테스트 계정 패널 노출 여부를 결정 — 운영 노출 주의.

## Backend Spring (`App/backend_spring`)
- Spring Boot 3.5.16 / Java. Gradle (`./gradlew`).
- web, validation, security, data-jpa, data-redis, AOP, retry.
- Flyway 마이그레이션(postgresql), springdoc OpenAPI, PDFBox, JJWT 0.13.
- 프로필: 운영은 `SPRING_PROFILES_ACTIVE=prod`. dev 프로필이면
  `/api/v1/auth/dev-login/*`과 Swagger가 열리므로 운영에서 절대 금지.

## Backend FastAPI (`App/backend_fastapi`)
- Python 3.12 / FastAPI 0.139 / Uvicorn 0.51 / Pydantic v2.
- 의존성 단일 기준은 **저장소 루트 `requirements.txt`** (Dockerfile과
  `App/scripts/run_ai_fastapi.sh` 모두 이걸 설치). backend_fastapi 하위에 두지 말 것.
- torch는 requirements.txt에 없다 — Dockerfile이 CPU 전용 인덱스로 먼저 설치한다.
  여기 명시하면 기본 PyPI에서 GPU 휠이 재설치되어 이미지가 수 GB 커진다.
- ML: scikit-learn, XGBoost, LightGBM, CatBoost, imbalanced-learn, MLflow(skinny).
- DL/임베딩: transformers, sentence-transformers, faster-whisper(STT, FFmpeg 별도).
- LLM: OpenAI SDK, ollama, langchain-core, langchain-huggingface, langsmith.
- 파일: pdfplumber, python-docx, python-pptx, reportlab.
- DB 접근: asyncpg, sqlalchemy, psycopg2-binary, pymongo.

## 데이터/인프라
- PostgreSQL 17 + **pgvector** (운영 이미지 `pgvector/pgvector:pg17`. 공식
  postgres:17에는 확장이 없어 마이그레이션이 깨진다).
- Redis 7, Kafka 3.8(KRaft 모드, zookeeper 불필요).
- Supabase Storage(산출물), MongoDB(ml_dashboard), Hugging Face Hub(모델 배포).
- 임베딩 모델은 리비전 고정: `HF_EMBEDDING_MODEL_REVISION`. 원격 갱신에 배포가
  조용히 끌려가지 않게 하려는 것 — 풀지 말 것.
