-- ============================================================================
-- WorkFlow AI - 마이페이지 "분야"를 다중 태그로 저장하도록 확장
-- 04_user_profile_fields.sql 이후에 실행됨.
-- ============================================================================

-- 기존 단일 문자열 값은 1개짜리 배열로 감싸서 보존한다.
ALTER TABLE users
    ALTER COLUMN field TYPE JSONB
    USING (CASE WHEN field IS NULL THEN '[]'::jsonb ELSE jsonb_build_array(field) END);

ALTER TABLE users ALTER COLUMN field SET DEFAULT '[]'::jsonb;
ALTER TABLE users ALTER COLUMN field SET NOT NULL;

COMMENT ON COLUMN users.field IS '전공/관심 분야 태그 배열 (예: ["백엔드", "인프라"])';
