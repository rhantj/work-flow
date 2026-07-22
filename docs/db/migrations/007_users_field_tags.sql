-- 마이페이지 "분야"를 단일 문자열이 아니라 여러 개의 태그로 입력할 수 있도록
-- users.field를 VARCHAR에서 JSONB 문자열 배열로 변경한다.
-- 기존 값은 1개짜리 배열로 감싸서 보존하며 데이터 손실은 없다.
-- 적용 대상: 현재 Supabase PostgreSQL (추후 OCI 자체 호스팅 이전 시 동일 스크립트 재실행)
--
-- ⚠ 이 마이그레이션은 010_users_field_tags_column.sql로 대체됐다 — field를 제자리에서
-- VARCHAR→JSONB로 바꾸는 파괴적 변경이라, 공유 DB에서 구버전 백엔드(field를 String으로 매핑)를
-- 기동 불가하게 만들 수 있었다. 신규 환경에서는 이 파일 대신 field_tags 컬럼을 새로 추가하는
-- 010을 적용할 것. 이 파일은 이미 적용된 환경의 이력 기록으로 남겨둔다.

-- data_type 체크로 감싸서 재실행해도 안전하게 한다. 이미 JSONB인 상태에서 그대로 다시 실행하면
-- jsonb_build_array가 배열을 한 겹 더 감싸 데이터가 이중 중첩되므로, 실제로 VARCHAR일 때만 변환한다.
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
