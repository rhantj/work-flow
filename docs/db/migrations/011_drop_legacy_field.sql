-- users.field(레거시) 컬럼 제거.
--
-- field_tags(010_users_field_tags_column.sql)가 이 컬럼을 완전히 대체했고, 어떤 코드도 더 이상
-- field를 참조하지 않는다. "미사용 상태로 남겨둔다"는 이전 설명이 스키마 문서/마이그레이션
-- 사이에서 계속 혼동(및 모순처럼 보이는 서술)을 일으켜서, 남겨두는 대신 실제로 지운다.
-- ADD COLUMN이 아니라 DROP이라 재실행해도 안전하다(IF EXISTS).
-- 적용 대상: 현재 Supabase PostgreSQL (추후 OCI 자체 호스팅 이전 시 동일 스크립트 재실행)
--
-- 배포 순서 주의: field_tags를 쓰지 않는 구버전 백엔드가 아직 떠 있는 동안 이 스크립트를 먼저
-- 실행하면 안 된다 — 여러 백엔드 인스턴스가 공유 DB에 동시 접속하는 롤링 배포 상황이라면, 반드시
-- 모든 인스턴스가 field_tags 기반 코드(현재 버전)로 교체된 뒤에만 이 마이그레이션을 실행할 것.

ALTER TABLE users DROP COLUMN IF EXISTS field;
