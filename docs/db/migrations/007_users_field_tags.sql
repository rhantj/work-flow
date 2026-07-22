-- 마이페이지 "분야"를 단일 문자열이 아니라 여러 개의 태그로 입력할 수 있도록
-- users.field를 VARCHAR에서 JSONB 문자열 배열로 변경한다.
-- 기존 값은 1개짜리 배열로 감싸서 보존하며 데이터 손실은 없다.
-- 적용 대상: 현재 Supabase PostgreSQL (추후 OCI 자체 호스팅 이전 시 동일 스크립트 재실행)

ALTER TABLE users
    ALTER COLUMN field TYPE JSONB
    USING (CASE WHEN field IS NULL THEN '[]'::jsonb ELSE jsonb_build_array(field) END);

ALTER TABLE users ALTER COLUMN field SET DEFAULT '[]'::jsonb;
ALTER TABLE users ALTER COLUMN field SET NOT NULL;

COMMENT ON COLUMN users.field IS '전공/관심 분야 태그 배열 (예: ["백엔드", "인프라"])';
