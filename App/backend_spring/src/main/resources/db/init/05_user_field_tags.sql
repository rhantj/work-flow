-- ============================================================================
-- WorkFlow AI - 마이페이지 "분야"를 다중 태그로 저장하도록 확장
-- 04_user_profile_fields.sql 이후에 실행됨.
--
-- ⚠ 이 파일은 08_users_field_tags_column.sql로 대체됐다 — field를 제자리에서 VARCHAR→JSONB로
-- 바꾸는 파괴적 변경이라, 공유 DB에서 구버전 백엔드(field를 String으로 매핑)를 기동 불가하게
-- 만들 수 있었다. 신규 환경에서는 이 파일 대신 field_tags 컬럼을 새로 추가하는 08을 적용할 것.
-- 이 파일은 이미 적용된 환경(및 초기화 스크립트 순서 유지)을 위해 남겨둔다.
-- ============================================================================

-- 기존 단일 문자열 값은 1개짜리 배열로 감싸서 보존한다.
-- data_type 체크로 감싸서 재실행해도 안전하게 한다(이미 JSONB면 건너뛴다).
DO $$
BEGIN
    IF (
        SELECT data_type FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'field'
    ) IS DISTINCT FROM 'jsonb' THEN
        ALTER TABLE users
            ALTER COLUMN field TYPE JSONB
            USING (CASE WHEN field IS NULL THEN '[]'::jsonb ELSE jsonb_build_array(field) END);
    END IF;
END $$;

ALTER TABLE users ALTER COLUMN field SET DEFAULT '[]'::jsonb;
ALTER TABLE users ALTER COLUMN field SET NOT NULL;

COMMENT ON COLUMN users.field IS '전공/관심 분야 태그 배열 (예: ["백엔드", "인프라"])';
