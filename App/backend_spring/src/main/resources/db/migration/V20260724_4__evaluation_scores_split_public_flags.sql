-- Existing deployments do not re-run docker-entrypoint-initdb.d scripts.
-- Keep these changes additive/idempotent so Flyway can apply them before JPA validation.
--
-- 기존 is_public 하나로 기여 점수/총합·학점/심사 코멘트가 한꺼번에 공개되던 것을
-- 세 개의 독립 플래그로 분리한다. 기존 is_public=true였던 row는 컬럼명 변경만으로
-- contribution_public=true를 그대로 유지하고, final_public/comment_public은
-- 새 컬럼이라 기본값(false)으로 시작한다(과다 공개 방지 — 안전한 기본값).

ALTER TABLE evaluation_scores RENAME COLUMN is_public TO contribution_public;

ALTER TABLE evaluation_scores ADD COLUMN IF NOT EXISTS final_public BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE evaluation_scores ADD COLUMN IF NOT EXISTS comment_public BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE evaluation_scores ADD COLUMN IF NOT EXISTS comment TEXT;

COMMENT ON COLUMN evaluation_scores.contribution_public IS '기여 점수(왼쪽 기여도 테이블) 공개 여부';
COMMENT ON COLUMN evaluation_scores.final_public IS '학점 계산기 총합/심사자 점수/학점 공개 여부';
COMMENT ON COLUMN evaluation_scores.comment_public IS '심사 코멘트 공개 여부';
COMMENT ON COLUMN evaluation_scores.comment IS '심사자가 팀원에게 남기는 평가 코멘트';
