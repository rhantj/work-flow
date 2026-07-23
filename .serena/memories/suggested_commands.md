# 자주 쓰는 명령 (Darwin/macOS)

## 전체 기동 (Docker, 권장)
- 로컬: `cd App && docker compose up -d --build`
- 운영과 동일 구성: `cd App && docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
- 로그: `docker compose logs -f backend-fastapi` (서비스명: db, redis, kafka,
  backend-spring, backend-fastapi, frontend, certbot)
- 컨테이너명은 `workflow-*` 접두사 (`workflow-db`, `workflow-frontend` 등).

## 개별 실행
- `App/scripts/dev-all.sh` — 전체 개발 모드 기동
- `App/scripts/run_ai_fastapi.sh` — FastAPI만 (루트 requirements.txt 설치)
- `App/scripts/build_spring_backend.sh` / `run_spring_backend.sh` — Spring 빌드/실행
- 프론트: `cd App/frontend && npm run dev` (빌드 `npm run build`)

## 테스트
- FastAPI: `pytest App/backend_fastapi/tests`
- 프론트: `cd App/frontend && npm test` (vitest)
- Spring: `cd App/backend_spring && ./gradlew test`

## Git
- push 전 항상 `git pull`.
- 보호 브랜치라 직접 push 불가:
  `git checkout -b fix/<주제>` → `git push origin fix/<주제>` →
  `gh pr create --base dev`. push 시 PR이 자동 생성되는 경우가 있어
  `gh pr create`가 "already exists"로 실패할 수 있다 — 정상이며 기존 PR을 쓰면 된다.

## 운영 서버 (OCI)
- 접속: `ssh -i ~/.ssh/oci-key teamlead@161.33.132.66`
- 레포는 `/home/ubuntu/work-flow` (소유자 ubuntu). teamlead로는 sudo 필요하고
  git이 dubious ownership을 거부하므로 `git -c safe.directory=/home/ubuntu/work-flow` 사용.
- 상세는 `mem:deployment`.

## macOS 유의
- `timeout` 명령 없음 — ssh는 `-o ConnectTimeout=N` 사용.
- `pgrep -f` / `pkill -f` (BSD). `ls`, `grep`, `sed`도 BSD판이라 GNU 전용 플래그 주의.
- `.DS_Store` 커밋 금지.
