package com.workflowai.presence;

import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.stereotype.Component;

/**
 * 중간보고/시연용 접속 상태 레지스트리. 단일 인스턴스 서버 메모리 기반이며,
 * heartbeat가 TTL 안에 오지 않으면 자동 만료된다(비정상 종료 대비 - 완벽한 세션 정리는 아님).
 */
@Component
public class PresenceService {
    private static final Duration TTL = Duration.ofSeconds(40);

    private final Map<Long, Instant> lastSeenByUserId = new ConcurrentHashMap<>();

    /** 테스트 로그인 시도. 다른 곳에서 이미 접속 중(TTL 이내)이면 false를 반환하고 상태를 바꾸지 않는다. */
    public boolean tryAcquire(Long userId) {
        Instant now = Instant.now();
        Instant previous = lastSeenByUserId.merge(userId, now, (existing, candidate) ->
            isFresh(existing, candidate) ? existing : candidate
        );
        return previous.equals(now);
    }

    /** 로그인 유지(heartbeat). 세션이 만료되어 있었더라도 다시 활성화한다. */
    public void touch(Long userId) {
        lastSeenByUserId.put(userId, Instant.now());
    }

    /** 로그아웃 시 접속 상태 제거. */
    public void release(Long userId) {
        lastSeenByUserId.remove(userId);
    }

    public boolean isActive(Long userId) {
        Instant lastSeen = lastSeenByUserId.get(userId);
        return lastSeen != null && isFresh(lastSeen, Instant.now());
    }

    /** 주어진 후보 유저 중 현재 활성 상태인 유저 id만 반환한다. */
    public List<Long> activeUserIds(List<Long> candidateUserIds) {
        return candidateUserIds.stream().filter(this::isActive).toList();
    }

    private boolean isFresh(Instant lastSeen, Instant now) {
        return Duration.between(lastSeen, now).compareTo(TTL) < 0;
    }
}
