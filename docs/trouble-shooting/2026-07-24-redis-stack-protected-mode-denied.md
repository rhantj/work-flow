# redis-stack 교체 후 다른 컨테이너 연결이 전부 DENIED되는 문제

- 날짜: 2026-07-24
- 브랜치: `feature/ai_assistent`
- 관련: `App/docker-compose.yml`(redis 서비스 `command`)

## 배경

어시스턴트 LangGraph 체크포인터(`langgraph-checkpoint-redis` → redisvl)가 RediSearch/RedisJSON
모듈을 요구해, 공유 redis를 `redis:7-alpine` → `redis/redis-stack-server`로 교체했다.
redis-stack 엔트리포인트를 bare `redis-server`로 덮으면 모듈이 안 올라오므로 `--loadmodule`로
직접 로드하도록 `command`를 지정했다.

## 증상

- `redis-cli ping`(레디스 컨테이너 **내부**)은 `PONG` 정상.
- 그런데 fastapi/spring 등 **다른 컨테이너**에서의 모든 연결이 실패:
  - redis-py async: `ConnectionError: Error UNKNOWN while writing to socket. Connection lost.`
  - redis-py sync: `Error 104 while writing to socket. Connection reset by peer.`
- langgraph `asetup()`뿐 아니라 회의록 캐시(`core.cache.get_redis_client`)까지 전부 영향.

## 원인

raw 소켓으로 직접 찔러보니 서버가 명령에 이렇게 응답했다.

```
-DENIED Redis is running in protected mode because protected mode is enabled and no password is set
```

bare `redis-server`로 `command`를 덮으면서 **redis-stack 기본 설정(`protected-mode no`)이 사라졌다.**
Redis는 protected mode가 켜지면 loopback 외(=다른 컨테이너)에서 온 연결은 TCP는 받되 명령을 DENIED한다.
그래서 컨테이너 내부 `redis-cli`만 되고 cross-container는 전부 막혔다.

## 조치

호스트 포트는 이미 `127.0.0.1`로만 노출돼 외부 접근이 차단돼 있으므로(=docker 내부망 한정),
`command`에 `--protected-mode no`를 추가해 기존 alpine 동작을 복원했다.

```yaml
redis:
  image: redis/redis-stack-server:7.2.0-v11
  command:
    - redis-server
    - --loadmodule
    - /opt/redis-stack/lib/redisearch.so
    - --loadmodule
    - /opt/redis-stack/lib/rejson.so
    - --protected-mode
    - 'no'
    - --appendonly
    - 'yes'
    # ... 기존 튜닝 플래그 유지
```

## 검증

```bash
docker compose up -d --no-deps redis
# async ping / asetup / 회의록 캐시 모두 정상 확인
docker exec workflow-backend-fastapi python -c "import asyncio,redis.asyncio as R; asyncio.run(R.from_url('redis://redis:6379/0').ping())"
```

## 되돌리는 법

`--protected-mode no`를 제거하면 다시 cross-container가 막힌다. 되돌리려면 대신 비밀번호
(`--requirepass`)를 설정하고 각 클라이언트의 `REDIS_URL`에 자격을 넣어야 한다.

## 교훈

redis-stack의 `command`를 통째로 덮을 때는 이미지 기본 설정(`/etc/redis-stack.conf`의
`bind * -::*`, `protected-mode no`)이 함께 사라진다는 점을 기억한다. 모듈 로드 플래그만
챙기면 되는 게 아니라 접근 제어 관련 기본값도 직접 복원해야 한다.
