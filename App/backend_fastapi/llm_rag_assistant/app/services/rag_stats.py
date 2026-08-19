"""어시스턴트 질의 집계 카운터.

## 왜 있는가

라우팅과 중복 제거를 넣었지만 **효과를 모른다.** 코드가 든 질문이 실사용에서 몇 %인지
모르므로 다음 투자처를 정할 수 없다. 설계와 답해야 할 다섯 질문은
docs/decisions/2026-08-01-assistant-query-observability.md 에 있다.

## 왜 로그가 아니라 Redis 인가

운영 컨테이너 로그는 **재배포마다 초기화된다**(로그 수집 인프라 없음, 배포는 하루 여러 번).
축적이 목적이므로 로그로는 안 된다. Redis 는 `appendonly yes` + `/data` 볼륨이라 살아남고,
스키마 변경이 없어 마이그레이션·승인 게이트 없이 바로 쌓기 시작할 수 있다.

## 질의 로그(query_log_service)와의 경계

이 모듈은 **수치만** 센다. 원문은 query_log_service 가 Postgres 에 따로 남긴다
(#627). 경계는 답해야 할 질문으로 갈린다 - 비중·추세는 여기, "어떤 문장이었나"를
봐야만 답할 수 있는 것(코드 없는 고유명사 질문의 검색 실패율)은 그쪽이다.
집계로 답할 수 있는 것을 로그에서 다시 세지 않는다. 두 곳에서 같은 것을 세면
어긋났을 때 어느 쪽이 맞는지 알 수 없다.

## 왜 이 모듈로 떼어냈나

Redis 세부와 실패 처리를 한 곳에 가둔다. 그래야 retrieval_service 가 캐시 인프라를 직접
알지 않고, 집계 필드 계산(_counter_fields)을 Redis 없이 단위 테스트할 수 있다.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone

from core.cache import get_async_redis_client

logger = logging.getLogger(__name__)

# 우선순위를 정하기 위한 몇 주짜리 측정이지 영구 텔레메트리가 아니다. 90일이면 계절성 없이
# 판단하기에 충분하고, 잊고 방치해도 스스로 사라진다.
_TTL_SECONDS = 90 * 24 * 60 * 60

# 코드 개수 버킷의 상한. 이 값 이상은 codes_5plus 한 칸에 모은다. top_k 기본값이 5라
# 5개를 넘게 나열하면 어차피 잘리므로, 그 이상은 개수를 세도 결정에 쓰이지 않는다.
_CODE_BUCKET_CAP = 5

# 답을 만든 백엔드별 카운터의 접두사. generation_service 의 프로바이더 이름이 그대로 붙는다.
_PROVIDER_FIELD_PREFIX = "provider_"

# 캐시에서 바로 돌려준 질의의 카운터. total 과 나눠 세는 이유는 record_cache_hit 에 적었다.
_CACHE_HIT_FIELD = "cache_hit"

# 통계 쓰기 한 번에 허용하는 시간. 예외를 삼키는 것만으로는 부족하다 - Redis 가 죽지 않고
# 느려지기만 하면 그 지연이 그대로 답변 지연이 된다. 집계는 부수적이므로 기다리지 않는다.
#
# 같은 컨테이너망의 Redis 파이프라인 1회는 밀리초 단위라 500ms 는 정상 왕복보다 두 자릿수
# 크다. 이보다 크게 잡을 이유가 없다 - 부수적인 계측이 답변을 붙잡는 시간이고, 여기서 넘긴
# 만큼은 그대로 사용자가 기다리는 시간이다. 상한을 넘긴 질의는 집계만 빠지고 답은 정상이다.
_WRITE_TIMEOUT_SECONDS = 0.5

# 한 질의가 쓸 날짜 키. pinned_stats_day 안에서만 채워진다. 두 경로에서 각각 다른 이유로
# 안전하다: HTTP 요청은 질의마다 별도의 asyncio Task 라 컨텍스트가 복제돼 동시 질의끼리
# 섞이지 않고, 한 Task 를 재사용하며 잡을 하나씩 처리하는 큐 워커(RagQueueWorker._run_loop)는
# pinned_stats_day 의 finally 가 매번 되돌리므로 앞 잡의 날짜가 다음 잡에 남지 않는다.
_pinned_stats_key: ContextVar[str | None] = ContextVar("rag_stats_pinned_key", default=None)


@dataclass(frozen=True)
class QuestionQueryStats:
    """질문 한 건에서 관측한 값. 집계에 필요한 수치만 담는다.

    질문 원문도 코드 값도 담지 않는다 - 다섯 질문이 전부 집계라 원문이 필요 없고,
    담지 않으면 개인정보 문제가 설계에서 통째로 사라진다.
    """

    project_id: int
    top_k: int
    personal: bool
    source_count: int
    code_count: int = 0
    code_hits: int = 0
    # 정확 일치에 내준 칸 수. id 지칭과 본문 코드가 함께 쓴다.
    code_slots: int = 0
    # 코드 검색이 예외로 실패한 경우. code_hits 가 0 이어도 "코드가 정말 없음"이 아니므로
    # code_miss 로 세면 안 된다. 두 가지를 한 칸에 담으면 관측값이 오염된다.
    code_search_failed: bool = False
    # 표시용 코드(TASK-230)·"230번"으로 지목된 업무 id. 본문 코드와 따로 센다 - 한 칸에
    # 담으면 "화면을 보고 지칭한 것"과 "제목에 우연히 코드가 든 것"을 구분할 수 없고,
    # 그 둘은 다음 투자처를 정할 때 정반대의 결론을 가리킨다.
    id_count: int = 0
    id_hits: int = 0


def _code_bucket(code_count: int) -> str:
    if code_count >= _CODE_BUCKET_CAP:
        return f"codes_{_CODE_BUCKET_CAP}plus"
    return f"codes_{code_count}"


def _counter_fields(stats: QuestionQueryStats) -> dict[str, int]:
    """올릴 필드 목록. 순수 함수라 Redis 없이 조건을 검증할 수 있다."""
    fields = {"total": 1, f"proj_{stats.project_id}": 1}

    if stats.personal:
        # 개인화 질문에는 라우팅을 걸지 않으므로(retrieval_service 참고) 코드 관련 필드를
        # 올리지 않는다. 올리면 "코드 질문 비중" 분모가 라우팅 미적용 경로까지 포함하게 된다.
        fields["personal"] = 1
    else:
        fields[_code_bucket(stats.code_count)] = 1
        if stats.code_count + stats.id_count > stats.code_slots:
            fields["codes_truncated"] = 1
        if stats.code_count > 0 and not stats.code_search_failed and stats.code_hits == 0:
            fields["code_miss"] = 1

        if stats.id_count > 0:
            fields["ids_referenced"] = 1
            # id 는 정수 정확 일치라 0건이면 그 업무가 이 프로젝트에 없다는 뜻이다.
            # 본문 텍스트 매칭인 code_miss 와 원인이 달라 따로 센다.
            if not stats.code_search_failed and stats.id_hits == 0:
                fields["id_miss"] = 1

    if stats.source_count < stats.top_k:
        fields["sources_short"] = 1

    return fields


def _stats_key(now: datetime | None = None) -> str:
    """rag_stats:{YYYY-MM-DD}. 날짜는 UTC 기준이다.

    서버 타임존 설정에 흔들리지 않기 위해서다. 해석할 때 KST 와 9시간 차이가 나므로
    KST 자정 전후 질의는 다른 날로 잡힌다(show_rag_stats.py 도 같은 기준으로 읽는다).
    """
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    return f"rag_stats:{stamp}"


@contextmanager
def pinned_stats_day() -> Iterator[None]:
    """이 블록 안에서 올리는 카운터를 전부 같은 날짜 키에 모은다.

    질문 카운터는 검색 직후에, 프로바이더 카운터는 생성이 끝난 뒤에 올라간다. 그 사이에는
    LLM 생성 시간(수 초)이 있어, 각자 날짜를 계산하면 UTC 자정을 넘긴 질의 한 건이 total 은
    어제 키에, provider_* 는 오늘 키에 남긴다. 그러면 어제는 분모만, 오늘은 분자만 늘어
    provider_* / total 이 양쪽 날 모두 틀어진다. 진입 시점의 날짜로 못 박아 막는다.
    """
    token = _pinned_stats_key.set(_stats_key())
    try:
        yield
    finally:
        _pinned_stats_key.reset(token)


async def record_question_query(stats: QuestionQueryStats) -> None:
    """질문 한 건을 집계한다."""
    await _increment_daily_counters(_counter_fields(stats))


async def record_answer_provider(provider: str) -> None:
    """답을 실제로 만든 백엔드를 집계한다.

    질문 카운터와 나눠 부르는 이유: 검색 시점에는 어느 백엔드가 답할지 아직 모른다.
    자동 모드는 HF -> Gemini -> Ollama 를 실제로 호출해 보고 첫 성공을 쓰므로
    (generation_service._generate_with_fallback_chain), 답이 나온 뒤에야 정해진다.
    total 과 같은 형식의 일별 키에 올려 provider_* / total 로 비중을 바로 읽는다.

    두 카운터가 **같은 날짜 키**에 들어가는 것은 호출부가 pinned_stats_day 로 감쌌을 때만
    보장된다(chat_service.answer_question 이 그렇게 부른다). 감싸지 않고 부르면 호출 시점의
    날짜를 쓰므로, 생성 중 자정을 넘긴 질의에서 분모와 분자가 다른 날에 흩어진다.
    """
    await _increment_daily_counters({f"{_PROVIDER_FIELD_PREFIX}{provider}": 1})


async def record_cache_hit() -> None:
    """캐시에서 바로 돌려준 질의 한 건을 집계한다.

    total 에 넣지 않고 별도 필드로 세는 이유: total 은 지금까지 캐시 미스만 세 왔고,
    같은 이름으로 다른 것을 세기 시작하면 이미 쌓인 일별 키와 비교할 수 없게 된다.
    앞으로 전체 질의 수는 total + cache_hit 이다.

    **알려진 한계**: codes_* 같은 버킷 필드는 검색이 돌아야 계산되므로 캐시 히트에서는
    낼 수 없다. 코드 분포는 여전히 캐시 미스만 본다. 이 카운터의 목적은 그 사각지대의
    크기를 알려주는 것이다 - 캐시 히트가 5% 면 분포를 그대로 믿어도 되고, 50% 면
    그때 검색 없이 버킷을 계산하는 방법에 투자한다.
    """
    await _increment_daily_counters({_CACHE_HIT_FIELD: 1})


async def _increment_daily_counters(fields: dict[str, int]) -> None:
    """일별 키의 필드들을 올린다. **어떤 경우에도 질의를 실패시키지 않는다.**

    날짜는 pinned_stats_day 안이면 그 블록이 못 박은 날, 밖이면 호출 시점의 날이다.

    advance_rag_project_epoch 가 이미 같은 정책이다("캐시는 DB 원본의 파생물이므로 무효화
    실패가 원본 변경 API를 실패시켜서는 안 된다"). 통계는 그보다도 부수적이다.

    호출부는 이 왕복을 응답 경로에서 그대로 await 한다. record_question_query 부터 쓰던
    정책 그대로다. 별도 태스크로 떼어내지 않는 이유는 그쪽이 유실·순서 뒤섞임을 대신
    떠안기 때문이고, 바꾼다면 모든 카운터를 함께 바꾼다.

    그래서 예외를 삼키는 것만으로는 부족하다. Redis 가 죽으면 즉시 예외가 나 답변이 그대로
    나가지만, **죽지 않고 느려지기만 하면** 그 지연이 고스란히 답변 지연이 된다. 삼킬 대상이
    생기지 않으므로 위 정책이 작동하지 않는 구간이다. 타임아웃으로 상한을 둔다 -
    asyncio.TimeoutError 도 Exception 이라 아래 except 가 그대로 받아 집계만 누락된다.
    """
    key = _pinned_stats_key.get() or _stats_key()
    try:
        # transaction=False 는 필수다. redis-py 기본값(True)은 MULTI/EXEC 로 감싸는데
        # fastapi ACL 계정에는 그 두 명령이 없어 통째로 NOPERM 이 된다. 원자성도 필요 없다 -
        # 필드마다 독립적인 HINCRBY 이고, 부분 실패해도 다음 질의가 이어서 센다.
        pipe = get_async_redis_client().pipeline(transaction=False)
        for field, amount in fields.items():
            pipe.hincrby(key, field, amount)
        # 매번 다시 건다. 키가 만들어진 날이 아니라 마지막으로 쓰인 날부터 90일이 되지만,
        # 일별 키라 그 차이는 하루뿐이고 TTL 이 빠지는 사고를 원천 차단하는 편이 낫다.
        pipe.expire(key, _TTL_SECONDS)
        await asyncio.wait_for(pipe.execute(), timeout=_WRITE_TIMEOUT_SECONDS)
    except Exception:
        logger.warning("질의 통계 기록 실패, 집계만 누락되고 답변은 정상 진행합니다.", exc_info=True)
