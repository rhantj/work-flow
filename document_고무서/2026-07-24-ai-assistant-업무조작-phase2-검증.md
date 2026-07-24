# AI 어시스턴트 업무 조작 기능 — Phase 2 런타임 검증 결과

- 날짜: 2026-07-24
- 브랜치: `feature/ai_assistent`
- 대상: LangGraph 실행 그래프(플래너·task_resolver·human-in-the-loop interrupt·Redis 체크포인터·resume)
- 환경: docker compose (fastapi / spring / frontend / redis-stack / postgres)
- 로그인: 데모 프로젝트, 허영주(팀장/LEADER)

## 기능 검증 (전부 통과)

| 항목 | 방법 | 결과 |
|---|---|---|
| 분류 라우팅 | 질문 5 + 명령 3 직접 호출 | 8/8 (질문→answer, 명령→명령 그래프) |
| Happy path | 브라우저에서 명령→실행 | 확인카드→실행→DB `#58 todo→done` |
| 모호성 처리 | 중복 제목 업무 지칭 | "어떤 업무인가요?" 되묻기(후보 나열) |
| 권한 차단 | MEMBER가 delete_task 시도 | "이 작업은 팀장 권한이 필요합니다" 차단, 카드 없음 |
| 실패 경로 | confirm 후 resume(ok=False) | "작업을 완료하지 못했습니다: …" + DB 무변경 |

### Happy path 상세 (브라우저 end-to-end)

1. 입력: "로그인 refresh logout API 구현 업무를 완료로 바꿔줘"
2. 분류→명령 그래프→플래너(change_status)→task_resolver가 #58 단일 매칭(임베딩 유사도)
3. interrupt로 확인 카드 표시: "업무 상태 변경 / WF-203 → 완료 / [실행][취소]"
4. 실행 클릭 → 프론트가 자기 JWT로 Spring API 호출(브라우저-실행자 패턴)
5. resume → "1개 작업을 완료했습니다."(type=done)
6. DB 확인: `tasks.id=58` status `todo` → `done`

FastAPI는 DB를 직접 건드리지 않고, 상태 변경은 프론트→Spring 경로로만 일어남을 확인.

### 실패 경로 상세

- confirm 수신 후 `resume(ok=False, error="모의 실행 실패")` → type=done,
  message="작업을 완료하지 못했습니다: 모의 실행 실패(권한/네트워크)"
- 실패 통보 시 DB(#58)는 그대로 → 부분 반영/유령 변경 없음.

## 인프라 이슈 3건 (검증 중 발견·해결, 코드 버그 아님)

1. **redis-stack protected-mode**: bare `redis-server` 오버라이드로 기본 설정이 사라져
   cross-container 연결이 전부 DENIED. `--protected-mode no` 추가로 복원.
   → `docs/trouble-shooting/2026-07-24-redis-stack-protected-mode-denied.md`
2. **HF 임베딩 모델 2.2GB 재다운로드/정체**: 캐시 볼륨 부재 + HF 네트워크 스로틀.
   `hf-cache` named volume 추가 + 재시도 루프로 완전 다운로드.
   → `docs/trouble-shooting/2026-07-24-fastapi-임베딩모델-재다운로드-정체.md`
3. **낡은 프론트 번들**: nginx가 Phase 2 이전 빌드 서빙 → 확인 카드 코드 부재.
   프론트 재빌드로 해결.
   → `docs/trouble-shooting/2026-07-24-frontend-stale-bundle-confirm-card.md`

## 알아둘 점 (후속 개선 후보, 이번 범위 아님)

- 플래너가 일부 표현("이름을 △△로 바꿔줘"=rename_task, "마감일을 …"=set_due_date)에서
  액션을 못 만들어 되묻기로 빠졌다. 권한 차단 자체는 delete_task로 명확히 검증됨.
- 데모 DB에 "…재검증 테스트 삽입" 중복 제목 업무가 많아, 단일 매칭 확인 카드를 보려면
  제목이 고유한 업무를 지칭해야 한다(모호하면 되묻기).
- RAG(질문) 경로의 "진행 중 목록 알려줘"류 집계성 질문은 의미검색 특성상 "근거 없음"이
  나올 수 있다(설계된 안티-할루시네이션). 상태별 목록은 대시보드/보드가 담당.

## 미커밋 변경

- `App/docker-compose.yml`: redis-stack 교체 + `--protected-mode no` + `hf-cache` 볼륨
  (frontend 재빌드는 이미지 재생성이라 커밋 대상 아님)
