-- 어시스턴트 질의 로그. "코드 없는 고유명사 질문의 검색 실패율"을 재기 위한 최소 항목만 담는다.
-- 결정과 근거: docs/decisions/2026-08-19-assistant-query-logging.md (#626, 2026-08-18 대표 승인).
-- 쓰는 곳은 FastAPI query_log_service 하나뿐이고, 읽는 경로는 앱·API로 만들지 않는다 -
-- 운영 DB 직접 조회만이다(조회 SQL은 query_log_service 모듈 주석에 있다).
--
-- user_id 와 답변 원문은 일부러 없다. 실패율 분석에 필요 없고, 빼면 "누가 무엇을 물었나"가
-- 재구성되지 않아 개인정보 부담이 크게 준다. 컬럼을 늘리기 전에 위 결정을 먼저 뒤집어야 한다.
-- 질문 본문의 이메일·전화번호는 저장 전에 애플리케이션이 치환한다.
--
-- 운영 적용은 자동이 아니다. spring.flyway.enabled 기본값이 false라
-- (application.yml) 적용 여부를 눈으로 확인해야 한다.
CREATE TABLE IF NOT EXISTS assistant_query_log (
    id         BIGSERIAL PRIMARY KEY,
    project_id BIGINT      NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    question   TEXT        NOT NULL,
    source_ids BIGINT[]    NOT NULL DEFAULT '{}',
    provider   VARCHAR(32) NOT NULL,
    created_at TIMESTAMP   NOT NULL DEFAULT NOW()
);

-- 보존기간 90일. 쓸 때마다 만료 행을 지우는 DELETE 가 이 인덱스를 탄다
-- (query_log_service._INSERT_SQL). 인덱스가 없으면 질의마다 전체 스캔이 답변 경로에 붙는다.
CREATE INDEX IF NOT EXISTS idx_assistant_query_log_created_at
    ON assistant_query_log (created_at);
