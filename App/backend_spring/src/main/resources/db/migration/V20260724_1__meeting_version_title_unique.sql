-- 회의록 수정본(버전) 제목 중복 방지: 애플리케이션 레벨 비관적 락(FOR UPDATE)만으로는
-- 락 조회 경로에 예외적인 빈틈이 생기면 중복 제목이 만들어질 수 있어, DB 유일성 제약으로
-- 이중 안전장치를 둔다. 같은 원본(original_meeting_id) 아래에서는 제목이 유일해야 한다.

-- 유니크 인덱스 생성이 기존 중복 데이터 때문에 배포 자체를 실패시키지 않도록,
-- 인덱스를 걸기 전에 이미 존재하는 중복 제목을 행별로 유일하게 보정한다.
-- (데이터를 지우지 않고 제목 뒤에 회의록 id를 붙여서만 구분한다.)
WITH duplicates AS (
    SELECT id,
           ROW_NUMBER() OVER (PARTITION BY original_meeting_id, title ORDER BY id) AS rn
    FROM meetings
    WHERE original_meeting_id IS NOT NULL
)
UPDATE meetings m
SET title = m.title || '_' || m.id
FROM duplicates d
WHERE m.id = d.id AND d.rn > 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_meetings_original_id_title
    ON meetings (original_meeting_id, title)
    WHERE original_meeting_id IS NOT NULL;
