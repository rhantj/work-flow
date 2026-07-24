# 확인 카드가 안 뜨는 문제 — 실은 프론트 낡은 번들

- 날짜: 2026-07-24
- 브랜치: `feature/ai_assistent`
- 관련: `App/frontend`(nginx 정적 서빙), `App/docker-compose.yml`(frontend 서비스)

## 증상

어시스턴트에 업무 조작 명령을 입력하면 "아래 작업을 실행할까요?" 텍스트만 나오고,
실행/취소 버튼이 달린 확인 카드(`ConfirmActionCard`)가 렌더되지 않았다.

## 오해하기 쉬운 지점

카드 렌더 조건이 `m.card && m.threadId`라, 프론트 파싱/렌더 버그처럼 보인다. 하지만
백엔드~네트워크는 전부 정상이었다.

- FastAPI 직접 호출: `type=confirm`, `thread_id`, `card`(step_id/tool/task_id/args) 정상 포함.
- Spring 통과: `AssistantResponse` 레코드가 snake_case 그대로 통과.
- 프론트가 실제로 받은 응답(fetch 인터셉터로 캡처): `data.card`, `data.thread_id` 모두 존재.
- 프론트 **소스**(`assistantApi.ts` toCard, `AIAssistant.tsx` 카드 attach/render)도 정상.

## 원인

실행 중인 `workflow-frontend` 컨테이너는 **Vite dev(HMR)가 아니라 nginx로 정적 빌드 번들을 서빙**한다.
그 번들이 오늘 이전(03:40) 빌드본이라, Phase 2에서 추가한 카드 렌더/실행/resume 코드가
번들에 아예 없었다.

```bash
# 서빙 중인 번들에 카드 로직 문자열이 있는지로 판별
docker exec workflow-frontend sh -c 'grep -rl "취소했습니다" /usr/share/nginx/html/assets'
# 낡은 번들: 0건, 재빌드 후: 1건
docker exec workflow-frontend sh -c 'ls -la /usr/share/nginx/html/assets/index-*.js'  # 빌드 시각 확인
```

즉 코드 버그가 아니라 **컨테이너에 반영 안 된 낡은 번들**이 원인이었다.

## 조치

프론트 이미지를 재빌드했다.

```bash
docker compose up -d --build frontend
```

재빌드 후(15:11 빌드) 번들에 카드 코드가 포함됐고("취소했습니다" 등 문자열 존재),
페이지 새로고침 시 확인 카드가 정상 렌더됐다. 실행→resume→DB 반영까지 end-to-end 확인.

## 교훈

- 프론트는 정적 빌드 서빙이다. **소스 파일을 고쳐도 재빌드 전에는 실행 화면에 반영되지 않는다.**
  `git`에 커밋됐는지와 별개로 컨테이너 번들이 최신인지 확인해야 한다.
- 프론트 관련 동작 이상은 코드 파싱을 파기 전에 먼저 "서빙 번들이 최신인가"를 확인한다.
  판별: nginx docroot의 `assets/*.js` 빌드 시각 + 기능 고유 문자열 grep.
