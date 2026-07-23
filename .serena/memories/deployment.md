# 배포 · 운영 서버

## 파이프라인
`.github/workflows/deploy-oci.yml` — **`main` push에만 트리거**. dev 머지로는 배포 안 됨.

순서: SSH 접속 → `git tag -f deploy-previous HEAD` → `git reset --hard origin/main`
→ `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
→ `/api/v1/health` 헬스체크(10초 간격 20회) → 실패 시 `deploy-previous`로 자동 롤백
→ 롤백 후에도 실패하면 Slack 알림.

`concurrency: deploy-oci`로 동시 실행 방지.

## 서버
- `ssh -i ~/.ssh/oci-key teamlead@161.33.132.66` (도메인 `t3-workflow-ai.site`)
- 레포 경로 `/home/ubuntu/work-flow`, 소유자 `ubuntu`.
  `teamlead`는 uid 1002, sudo·docker 그룹 소속. 파일 접근에 sudo 필요.
- git 명령은 `git -c safe.directory=/home/ubuntu/work-flow ...` 로 감싸야 dubious
  ownership 거부를 피한다.
- 컨테이너 재빌드는 2분을 넘기므로 백그라운드로 돌릴 것.
- 재빌드 직후 수십 초간 502가 난다 — 실패로 단정하지 말고 재시도할 것.

## prod 오버레이의 요점 (`docker-compose.prod.yml`)
- 모든 내부 서비스를 `127.0.0.1`에만 바인딩. 외부 노출은 frontend의 80/443뿐.
  DB를 봐야 하면 SSH 터널(`-L 5432:localhost:5432`).
- `ports: !override`가 핵심 — 없으면 base의 0.0.0.0 게시가 append되어 남는다 (Compose v2.24+).
- db 이미지를 `pgvector/pgvector:pg17`로 교체 (공식 postgres:17엔 vector 확장 없음).
- spring에 `SPRING_PROFILES_ACTIVE=prod` 주입 — dev-login 엔드포인트와 Swagger 차단.
- nginx가 TLS 종료, certbot 컨테이너가 12시간마다 갱신, nginx는 6시간마다 reload.
  `/etc/letsencrypt` 전체를 마운트해야 live/의 상대 심볼릭 링크가 풀린다.

## 알려진 이슈
- Docker 빌드 캐시가 수 GB 쌓이는데 `image prune` / `builder prune`으로는
  0B만 회수된다(실행 중 이미지에 묶여 있음). `--all` 강제 정리는 위험하니 별도 판단.
