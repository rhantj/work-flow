"""어시스턴트 질의 로그.

## 왜 있는가

rag_stats 는 집계만 센다. 그것만으로는 답할 수 없는 질문이 하나 남았다 -
`output/hybrid_rag_eval/RESULT.md` 가 pg_trgm 하이브리드 도입을 보류한 이유,
**"코드 없는 고유명사 질문이 검색에서 얼마나 실패하는가"** 다. 코드가 0개인 질문은
집계에서 `codes_0` 한 칸에 뭉쳐 들어가고, 그 안에서 "고유명사가 핵심인 질문"과
"순수 개념 질문"은 문장을 보지 않으면 갈라낼 수 없다. 그래서 원문을 남긴다.

결정과 그 근거는 docs/decisions/2026-08-19-assistant-query-logging.md 에 있다.

## rag_stats 와의 경계

- rag_stats: 수치만, Redis, 원문 없음. 비중·추세를 본다.
- 이 모듈: 원문 포함, Postgres. **딱 위 한 가지 분석**을 위한 것이다.

집계로 답할 수 있는 것을 여기서 다시 세지 않는다. 두 곳에서 같은 것을 세면
어긋났을 때 어느 쪽이 맞는지 알 수 없다.

## 무엇을 담지 않는가

user_id 와 답변 원문을 담지 않는다. 실패율 분석에 필요 없고, 빼면 "누가 무엇을
물었나"가 재구성되지 않아 개인정보 부담이 크게 준다. 조회용 API·화면도 만들지
않는다 - 조회 경로를 만들면 그 경로의 인가를 또 지켜야 하고, 질문 원문에 대한 권한
검사는 한 번 틀리면 그대로 유출이다.

## 어떻게 읽는가

운영 DB에 SSH 터널로 붙어(운영 Postgres는 127.0.0.1:5432 만 바인딩) 직접 조회한다.
읽는 방법을 적어두지 않으면 이 테이블은 아무도 쓰지 않아 지워진 assistant_messages 의
재판이 된다. 목적인 "검색 실패율"은 다음 두 쿼리로 본다.

    -- 1) 검색이 한 건도 걸리지 않은 질문 (= 실패 사례. pg_trgm 판단의 근거)
    SELECT created_at, project_id, question
    FROM assistant_query_log
    WHERE cardinality(source_ids) = 0
    ORDER BY created_at DESC;

    -- 2) 프로젝트별 실패율. project_id = 1 은 데모 데이터가 섞여 있어 따로 본다.
    SELECT project_id,
           count(*) AS total,
           count(*) FILTER (WHERE cardinality(source_ids) = 0) AS empty_hits
    FROM assistant_query_log
    GROUP BY project_id ORDER BY total DESC;

## 끄는 법

`ASSISTANT_QUERY_LOG_ENABLED` 를 지우거나 false 로 둔다(기본값이 꺼짐이다).
코드 배포 없이 멈춘다 - 다만 환경변수는 프로세스 밖에서 바뀌지 않으므로 값 변경 뒤
컨테이너 재기동이 필요하다. 코드 변경·재빌드가 없다는 뜻이지 무중단이라는 뜻이 아니다.

**끈 뒤에는 남은 행이 스스로 사라지지 않는다.** 만료 삭제가 쓰기 경로에 얹혀 있어
(record_query_log 참고) 기록이 멈추면 삭제도 멈춘다. 질의가 아주 뜸한 기간도 마찬가지다.
끄면서 데이터까지 비우려면 한 줄을 직접 돌린다.

    DELETE FROM assistant_query_log;                                  -- 전부
    DELETE FROM assistant_query_log WHERE created_at < NOW() - INTERVAL '90 days';  -- 만료분만

## 켜기 전에

마이그레이션이 **먼저** 적용돼 있어야 한다. `spring.flyway.enabled` 기본값이 false 라
(application.yml) 테이블이 없는 채로 스위치만 켜면 질의마다 기록이 실패하고 경고 로그가
쌓인다. 답변은 정상이지만(실패를 삼킨다) 로그는 한 건도 남지 않는다.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from collections.abc import Sequence

logger = logging.getLogger(__name__)

# 켜는 쪽이 명시적이어야 한다. 질문 원문을 남기는 기능이 환경 설정 실수로 조용히 켜져
# 있는 것보다, 켜야 할 곳에서 안 켜져 있는 편이 낫다(WORKFLOW_MAIL_ENABLED 와 같은 형태).
# 되돌릴 때 코드 배포가 필요 없는 스위치이기도 하다.
_ENABLED_ENV = "ASSISTANT_QUERY_LOG_ENABLED"
_TRUTHY = {"1", "true", "yes", "on"}

# 보존기간. 이 로그의 소비자는 "분기 1회 하이브리드 재검토" 하나라 90일이면 재검토 주기를
# 한 번 덮는다. 그보다 오래된 질문은 제품이 바뀌어(업무 코드 형식, 청크 구성, 라우팅 동작)
# 지금 검색기의 실패율을 대변하지 못한다. rag_stats._TTL_SECONDS 도 같은 이유로 90일이다.
_RETENTION_DAYS = 90

# 질문 본문에 섞여 들어오는 연락처를 저장 전에 지운다. 지운 자리에 표식을 남기는 이유:
# 통째로 지우면 "연락처가 있었다"는 사실까지 사라져 분석할 때 문장이 왜 끊겼는지 알 수 없다.
_EMAIL_PLACEHOLDER = "[EMAIL]"
_PHONE_PLACEHOLDER = "[PHONE]"

_EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

# 한국 전화번호. 국번(0으로 시작하는 2~3자리) 또는 +82 국제 표기로 시작할 때만 잡는다.
# 앞뒤 숫자 경계를 두는 것은 마스킹 과잉을 막기 위해서다 - "2026-08-19", "230번" 같은
# 날짜·업무 번호까지 지우면 실패율을 재려고 남긴 원문이 정작 분석에 못 쓰게 된다.
#
# +82 뒤를 휴대전화 국번(10, 11, 16~19)으로 좁히지 않는 이유: 그러면 "+82-2-1234-5678"
# 같은 유선 국제표기가 통째로 샌다. 괄호를 구분자로 받는 이유도 같다 - "(010) 1234-5678",
# "02)1234-5678" 은 사람이 실제로 쓰는 표기인데, 안 받으면 마스킹이 조용히 비켜간다.
_PHONE_PATTERN = re.compile(
    r"(?<![0-9])\(?(?:\+?82[-. ]?|0)\d{1,2}\)?[-. ]?\d{3,4}[-. ]?\d{4}(?![0-9])"
)

# 로그 쓰기 한 번에 허용하는 시간. rag_stats._WRITE_TIMEOUT_SECONDS 와 같은 이유로 둔다 -
# 예외를 삼키는 것만으로는 부족하고, DB 가 죽지 않고 느려지기만 하면 그 지연이 그대로
# 답변 지연이 된다. 상한을 넘긴 질의는 로그만 빠지고 답은 정상이다.
#
# Redis 쪽(0.5초)보다 크게 잡는다. 같은 왕복 한 번이지만 이쪽은 풀에서 커넥션을 얻어
# INSERT 와 만료 행 삭제를 함께 도는 트랜잭션이라 정상 소요가 더 길다. 그래도 LLM
# 생성(수 초)보다 두 자릿수 작아, 최악의 경우에 붙는 지연이 답변을 붙잡지 않는다.
_WRITE_TIMEOUT_SECONDS = 1.0

# 만료 행 삭제를 INSERT 와 한 문장에 묶는다. 이유는 record_query_log 참고.
# 보존일수는 정수 상수라 문자열로 끼워 넣어도 주입 여지가 없다(파라미터로 넘기면
# 인터벌 캐스팅이 붙어 SQL 이 오히려 읽기 어려워진다).
_INSERT_SQL = f"""
WITH purged AS (
    DELETE FROM assistant_query_log
    WHERE created_at < NOW() - INTERVAL '{_RETENTION_DAYS} days'
)
INSERT INTO assistant_query_log (project_id, question, source_ids, provider)
VALUES ($1, $2, $3::bigint[], $4)
"""


def is_logging_enabled() -> bool:
    """호출할 때마다 환경변수를 본다. 모듈 로드 시점에 굳히면 컨테이너를 다시 띄우기 전에는
    끌 수 없어, "배포 없이 되돌린다"는 스위치의 목적이 사라진다."""
    return os.getenv(_ENABLED_ENV, "").strip().lower() in _TRUTHY


def mask_sensitive_text(text: str) -> str:
    """이메일·전화번호를 표식으로 바꾼다. 순수 함수라 DB 없이 검증할 수 있다."""
    masked = _EMAIL_PATTERN.sub(_EMAIL_PLACEHOLDER, text)
    return _PHONE_PATTERN.sub(_PHONE_PLACEHOLDER, masked)


async def record_query_log(
    pool,
    *,
    project_id: int,
    question: str,
    source_ids: Sequence[int],
    provider: str,
) -> None:
    """질의 한 건을 남긴다. **어떤 경우에도 답변을 실패시키지 않는다.**

    rag_stats._increment_daily_counters 와 같은 정책이다. 로그 저장이 답변을 죽이면
    관측을 붙이려다 기능을 잃는다.

    90일 초과 행은 이 쓰기가 함께 지운다. 별도 스케줄러를 두지 않는 이유:
    - 이 테이블에 쓰는 곳이 여기 하나뿐이라, 쓰기가 멈추면 더 쌓이지도 않는다.
      청소만 따로 살아 있어야 할 이유가 없다. 켜고 끄는 스위치와 지우는 주체가
      한 파일에 있어야 되돌릴 때 두 곳을 찾아다니지 않는다.
    - pg_cron 은 설치돼 있지 않고(저장소의 CREATE EXTENSION 은 vector 뿐), 확장 설치는
      공유 인프라 변경이라 이 목적에 과하다. Spring @Scheduled 는 동작하지만 쓰는 쪽과
      지우는 쪽이 다른 언어·다른 컨테이너로 갈린다.
    - 데이터 수정 CTE 는 INSERT 와 같은 왕복·같은 트랜잭션에서 돌아, "쓸 때마다 지운다"가
      추가 실패 지점 없이 성립한다. 질의량이 적어(청크 444건 규모) 하루치 삭제는
      created_at 인덱스로 즉시 끝난다.
    - 위 타임아웃에 걸려 통째로 취소돼도 다음 질의가 이어서 지운다. 삭제가 늦어질 뿐
      쌓이지는 않는다.
    """
    if not is_logging_enabled():
        return

    try:
        await asyncio.wait_for(
            _insert_log(pool, project_id, question, list(source_ids), provider),
            timeout=_WRITE_TIMEOUT_SECONDS,
        )
    except Exception:
        logger.warning("질의 로그 기록 실패, 로그만 누락되고 답변은 정상 진행합니다.", exc_info=True)


async def _insert_log(pool, project_id: int, question: str, source_ids: list[int], provider: str) -> None:
    # 마스킹도 타임아웃 안에서 한다. 호출부 인자로 빼면 wait_for 가 타이머를 걸기 전에
    # 동기로 돌아, 답변 경로가 붙잡히는 구간이 상한 밖에 남는다.
    async with pool.acquire() as conn:
        await conn.execute(_INSERT_SQL, project_id, mask_sensitive_text(question), source_ids, provider)
