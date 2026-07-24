-- ============================================================================
-- 기여도 분석 화면의 "평가 확정" 기능 지원 컬럼. additive/idempotent.
-- 기존에 떠 있는 DB에는 수동으로 psql -f 실행 필요
-- (docker-entrypoint-initdb.d는 볼륨이 비어있을 때만 자동 실행됨).
-- ============================================================================

ALTER TABLE projects ADD COLUMN IF NOT EXISTS eval_status VARCHAR(20) NOT NULL DEFAULT 'EVALUATING';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_projects_eval_status'
    ) THEN
        ALTER TABLE projects ADD CONSTRAINT chk_projects_eval_status
            CHECK (eval_status IN ('PENDING', 'EVALUATING', 'PUBLISHED'));
    END IF;
END $$;

COMMENT ON COLUMN projects.eval_status IS
    '프로젝트 평가 진행 상태(PENDING/EVALUATING/PUBLISHED). 심사자가 기여도 분석 화면에서 "평가 확정"을 누르면 PUBLISHED로 전이한다.';
