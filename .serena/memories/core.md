# Work-Flow — 프로젝트 개요

GitHub: `rhantj/work-flow`. 로컬: `/Users/gomuseo/Desktop/Python/Work-Flow`.
운영: https://t3-workflow-ai.site (OCI, `161.33.132.66`).

팀 프로젝트 협업/평가 보조 웹 플랫폼 "WorkFlow AI". 회의록 분석, RAG 챗봇,
기여도 산출, 지연 위험도 예측 등을 제공한다. **구현 완료되어 배포 운영 중이다.**

## 구조 — App/ 3계층 + 인프라

| 경로 | 역할 |
| --- | --- |
| `App/frontend` | React 19 + Vite SPA (`workflow-ai`). 도메인별 폴더: auth, board, dashboard, meetings, ai, contributors, deliverables, github, mypage |
| `App/backend_spring` | Spring Boot 3.5 API 서버. 인증/도메인/DB 소유. `/ai/*`로 FastAPI 호출 |
| `App/backend_fastapi` | AI 서버. LLM·ML·DL·임베딩 담당 |
| `App/docker-compose.yml` | 로컬 기동 (db/redis/kafka/spring/fastapi/frontend) |
| `App/docker-compose.prod.yml` | 운영 오버레이. 상세는 `mem:deployment` |
| `.github/workflows/deploy-oci.yml` | main push 시 자동 배포. 유일한 워크플로우 |

FastAPI 하위는 기능 단위로 쪼개져 있다: `llm_rag_assistant`, `llm_checklist`,
`ai_contribution_report`, `contribution_score`, `ml_delay_risk`,
`ml_workload_score`, `dl_sentence_classification`, `core`, `app`.

기타 최상위: `docs/`(기획·ERD·트러블슈팅), `convention/`(코딩 규약 원본),
`document_<이름>/`(개인 실험 정리), `supabase/`.

## 불변 규칙

- **push 전 `git pull` 필수.** 오류는 문제 난 브랜치에서 고쳐서 머지.
- **`dev`/`main`은 보호 브랜치.** 직접 push 불가 — feature 브랜치 → PR만 가능.
- 커밋·푸시·PR은 사용자가 명시적으로 요청할 때만.
- 파일 구조 변경·추가는 퍼미션 후 실행.
- 기술 스택 상세는 `mem:tech_stack`, 컨벤션은 `mem:conventions`,
  명령은 `mem:suggested_commands`, 완료 절차는 `mem:task_completion`,
  배포·운영 서버는 `mem:deployment`.
