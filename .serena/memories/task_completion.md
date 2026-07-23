# 작업 완료 시 절차

## 변경 파트별 확인
- **FastAPI**: `pytest App/backend_fastapi/tests` (해당 기능 하위 디렉터리만이라도).
  의존성 변경 시 루트 `requirements.txt`만 수정 — 다른 곳에 중복 정의 금지.
- **Spring**: `./gradlew test`. 스키마 변경은 Flyway 마이그레이션으로.
- **Frontend**: `npm test` + `npm run build` (타입/빌드 오류는 여기서 잡힌다).
- **compose/Dockerfile 변경**: 실제로 `docker compose up -d --build`까지 돌려
  컨테이너가 healthy로 올라오는지 확인. 빌드 성공 ≠ 기동 성공.

## Git 반영 전
1. `git pull`로 최신 반영.
2. `.env`, `.DS_Store`, 빌드 산출물(`build/`, `dist/`)이 스테이징에 없는지 확인.
3. feature/fix 브랜치에서 작업했는지 확인 (dev/main 직접 push 불가).
4. 커밋·푸시·PR은 **사용자가 명시적으로 요청할 때만**.

## 배포까지 가는 경우
- `main`에 머지되는 순간 `.github/workflows/deploy-oci.yml`이 실운영에 배포한다.
  dev 머지는 배포되지 않는다. 배포 흐름·롤백은 `mem:deployment`.

## 기록
- 해결에 시간이 걸린 문제는 `docs/trouble-shooting/YYYY-MM-DD-주제.md`로 남긴다.
- 아키텍처·의존성·데이터 모델·외부 연동이 바뀌면 `docs/decisions/`에 결정 기록.
- 구조가 바뀌었으면 이 serena 메모리도 같이 갱신할 것 (낡은 메모리는 없는 것보다 나쁘다).
