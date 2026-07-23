# 코딩 컨벤션

**원본은 `convention/ai.md`, `convention/backend.md`, `convention/frontend.md`.**
작업 전 해당 파트 파일을 읽을 것. 아래는 그 위에 얹히는 프로젝트 전역 규칙.

## 언어/스타일
- 주석·docstring·로그·문서·커밋 메시지 모두 **한국어**.
- 커밋: conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`, `chore:`) + 한국어 설명.
- 주석은 WHY가 자명하지 않을 때만. 요청 범위 밖 리팩터링·추상화 금지.

## 산출물 배치
- 실험/분석은 노트북(ipynb). 넘버링 `01`, 하위는 `01-1`.
- 산출물은 `output/` 하위(분류 자유). 없으면 생성.
- 실험 결과 정리는 `document_<사용자이름>/`에 md.
- **문제 해결 기록은 `docs/trouble-shooting/`에 `YYYY-MM-DD-주제.md`로 남긴다** (기존 관례).
- 보고서는 html/css 기반 ppt 슬라이드 형식.

## 보안 (중요)
- 시크릿 하드코딩 금지. `.env` / GitHub Secrets로 주입.
- `App/.env`는 gitignore. 운영 서버 `.env`는 별도 관리 — 커밋 대상 아님.
- 다음 값들은 서비스 간 공유 시크릿이라 양쪽이 반드시 일치해야 한다:
  `RAG_INTERNAL_API_KEY` (spring ↔ fastapi, `/ai/rag/*` 보호).
- `VITE_ENABLE_DEMO_AUTH=true`면 로그인 화면에 테스트 계정 7개가 노출된다.
  데모 목적의 의도된 설정이나, 운영 정책이 바뀌면 가장 먼저 꺼야 할 스위치.

## Git 워크플로우
- `dev`, `main`은 **보호 브랜치** — 직접 push하면 GH006으로 거부된다.
  항상 `feature/*` 또는 `fix/*` 브랜치에서 작업 → `gh pr create --base dev`.
- push 전 `git pull` 필수. 파괴적 명령(`reset --hard`, `push --force`)은 사전 확인.
- GitHub 계정 `rhantj`. `gh` CLI 사용.
