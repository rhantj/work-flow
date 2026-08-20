# 어시스턴트 평가 코퍼스 스냅샷

평가 케이스 30건(`../*.json`)이 근거로 삼는 문서 코퍼스다. 2026-08-20 에 동결 Supabase
프로젝트 1 에서 떴다.

## 왜 있는가

이 코퍼스는 **운영 OCI 에 존재하지 않는다.** 2026-08-20 실측 기준:

| | 동결 Supabase | 운영 OCI |
|---|---|---|
| 프로젝트 1 청크 | 308 | 0 |
| `WF-` 코드 포함 청크 | 다수 | 0 |

운영 OCI 의 프로젝트는 전부 2026-08-03 이후 새로 만들어진 것이라, 픽스처 30건이 의존하는
WF 코드가 하나도 없다. 그리고 Supabase 는 롤백용으로 동결된 뒤 2026-08-13 경 삭제 예정이었다.
삭제되면 픽스처의 근거가 재구성 불가로 사라진다. 그래서 레포로 옮겼다.

**주의:** 이 코퍼스로 잰 점수는 운영 검색 품질이 아니다. 데모 데이터셋의 점수다.
운영 데이터로 재앵커링할지는 별도 판단이다.

## 무엇이 들어 있나

| 파일 | 행수 | 내용 |
|---|---|---|
| `chunks.jsonl` | 308 | `id, source_type, source_id, content, assignee_id` |
| `tasks.jsonl` | 166 | `id, title, description, status, priority, assignee_id, due_date` |
| `meetings.jsonl` | 17 | `id` (액션아이템의 프로젝트 범위 조인에만 쓰인다) |
| `action_items.jsonl` | 66 | `id, meeting_id, due_date, priority, final_assignee_id` |
| `people.json` | 24 | `users`(id → 별칭) 10명, `transcript_only`(계정 없는 화자) 14명 |

컬럼은 어시스턴트가 실제로 읽는 것만 남겼다. `meetings.transcript`(회의 전문),
`users` 의 인증 컬럼(`password_hash`, `email`, `phone` 등)은 뜨지 않았다.

### 임베딩이 없는 이유

벡터를 저장하면 3.4MB, 본문만 두면 119kB 다. 임베딩 모델이 API 가 아니라 리비전 고정된
로컬 SentenceTransformer(`rhantj/bge-m3-workflow-query-robust` @ `dc32873`)라 같은 본문에서
같은 벡터가 나오므로, 적재할 때 다시 만든다.

이게 성립한다는 건 추측이 아니라 측정으로 확인했다 — 아래 검증 절차 참고.

### 실명 처리

사람 이름은 전부 `구성원A`~`구성원X`(24명)로 치환했다. 출처가 두 갈래다.

- **`users` 10명** — 담당자이거나 본문에 이름이 나오는 계정. `people.json` 의 `users`.
- **계정 없는 화자 14명** — 회의록 화자 표기(`이름:`)와 참석자 목록에만 나온다.
  `users` 를 조회해서는 절대 안 걸리므로 추출기의 `EXTRA_NAMES` 에 손으로 확인해 넣었다.
  `people.json` 의 `transcript_only`.

같은 규칙을 **코퍼스·케이스 픽스처 9개·검색 평가셋**(`output/hybrid_rag_eval/data/evalset.json`)에
한꺼번에 적용했다. 한쪽만 치환하면 픽스처와 평가셋을 1:1 로 대조하는 테스트가 깨지고,
사실 문장과 근거 발췌가 어긋난다.

치환 규칙에서 걸린 것 두 가지.

- **한글 경계** — 2자 이름이 보통 낱말 안에서 잘리지 않게 앞뒤 한글을 배제한다.
- **조사** — 한국어는 이름에 조사가 바로 붙는다(이름 뒤에 `은`·`으로` 가 바로 붙는다). 조사를 허용하지 않으면 조사가
  붙은 쪽만 치환에서 빠져, 사실 문장과 근거가 서로 다른 사람을 가리키게 된다.
  `test_dataset.mentions_person` 과 같은 조사 목록을 쓴다.

별칭에 라틴 문자가 붙어 있어서 `test_dataset.py` 의 인물 패턴(`SPEAKER_PATTERN`,
`ASSIGNEE_PATTERN`)도 함께 넓혔다. 한글만 잡으면 별칭이 하나도 안 걸려 인물 규칙이
아무것도 안 하는 채로 통과한다. 넓힌 뒤 캐지는 인물 수는 9명으로 치환 전과 같다.

치환 후에도 점수는 움직이지 않았다(아래 검증 결과 참고).

`test_corpus_snapshot.py` 가 두 겹으로 막는다.

- 화자·참석자 자리에 별칭도 일반 낱말도 아닌 한글이 나오면 실패한다.
- **실명 21개의 해시와 대조**한다. 코퍼스·케이스 픽스처·검색 평가셋·이 문서를 전부 훑어,
  한글 토막이 그 해시에 걸리면 실패한다. 위치 기반 검사만으로는 부족했다 - 실제로
  `담당을 <이름>으로` 형태는 이름이 `담당` **뒤**에 와서 어느 패턴에도 안 걸렸다.
  해시는 비밀이 아니다(소금이 같은 파일에 있다). 목록을 눈에 안 띄게 둘 뿐이다.

## 쓰는 법

```bash
docker run -d --name workflow-eval-db -p 55432:5432 \
  -e POSTGRES_PASSWORD=eval -e POSTGRES_DB=eval pgvector/pgvector:pg17

cd App/backend_fastapi
EVAL_DATABASE_URL=postgres://postgres:eval@localhost:55432/eval \
  python scripts/seed_eval_corpus.py
```

시딩 스크립트는 테이블을 DROP 후 재생성한다. 방어선이 두 겹이다.

1. 호스트명이 로컬이 아니면 거부한다.
2. **대상 DB 에 직접 물어본다** — 비어 있거나 이 스크립트가 남긴 마커
   (`eval_corpus_marker`)가 있을 때만 진행한다.

2번이 실질 방어선이다. 이 팀은 운영 OCI 에 SSH 터널(`-L <port>:localhost:5432`)로 붙으므로
**운영 DB 도 종단은 문자 그대로 `localhost`** 다. 호스트명만으로는 구분할 수 없다.

## 검증

적재 결과가 원본과 같은지는 기존 게이트 스크립트로 확인한다.

```bash
# HF 토큰이 들어가므로 남이 읽을 수 없는 파일에 쓴다. /tmp 에 그냥 만들면 공유 머신에서
# 다른 사용자가 읽는다.
ENV_FILE=$(mktemp) && chmod 600 "$ENV_FILE"
printf 'DATABASE_URL=postgres://postgres:eval@localhost:55432/eval\n' > "$ENV_FILE"
grep '^HF_' ../.env >> "$ENV_FILE"
ASSISTANT_EVAL_ENV_FILE="$ENV_FILE" python scripts/recompute_grounding.py
rm -f "$ENV_FILE"
```

2026-08-20 실행 결과 — 동결 Supabase 원본과 완전히 일치했다.

```
분류               id 전용       본문 포함        차이
identifier       1.000       1.000    +0.000
mixed            0.950       0.950    +0.000
semantic         0.400       0.433    +0.033
전체               0.783       0.794    +0.011

점수가 달라진 케이스 1건
  semantic-09    0.00 -> 0.33   본문으로만 잡힌 사실 ['F1']

코퍼스: 청크 308건 (기준 308건)
[OK] id 전용 전체 0.783 로 RESULT.md 기록과 일치한다.
```

`[경고]` 가 나오면 스냅샷이 원본과 어긋난 것이다. 그때는 본문 재임베딩 전제가 깨진 것이므로
벡터까지 저장하는 방식으로 되돌려야 한다.

## 다시 뜨려면

원본이 살아 있는 동안만 가능하다. 뽑은 쿼리는 다음과 같다(프로젝트 1 기준).

```sql
SELECT id, source_type, source_id, content, assignee_id
  FROM document_chunks WHERE project_id = 1 ORDER BY id;
SELECT id, title, description, status, priority, assignee_id, due_date
  FROM tasks WHERE project_id = 1 ORDER BY id;
SELECT id FROM meetings WHERE project_id = 1 ORDER BY id;
SELECT ai.id, ai.meeting_id, ai.due_date, ai.priority, ai.final_assignee_id
  FROM meeting_action_items ai JOIN meetings m ON m.id = ai.meeting_id
  WHERE m.project_id = 1 ORDER BY ai.id;
```

## 알려진 한계

`project_stats_service` 의 마감일 쿼리는 `CURRENT_DATE` 를 쓴다. 스냅샷의 `due_date` 는
고정이므로 "마감 임박" 계열 답변은 **실행 날짜에 따라 달라진다.** 근거 채점
(`recompute_grounding.py`)은 검색만 돌려서 영향받지 않지만, 베이스라인 노트북으로 답변까지
생성할 때는 이 점을 감안해야 한다. 스냅샷 이전부터 있던 성질이다.
