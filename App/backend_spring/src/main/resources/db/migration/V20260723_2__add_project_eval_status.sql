-- Existing deployments do not re-run docker-entrypoint-initdb.d scripts.
-- Keep these changes additive/idempotent so Flyway can apply them before JPA validation.

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
