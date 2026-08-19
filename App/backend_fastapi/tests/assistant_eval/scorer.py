"""답변의 근거가 실제로 있었는지를 기계적으로 채점한다.

LLM 을 쓰지 않는다. 출처는 식별자 집합이라 결정적으로 대조할 수 있고, 그래야 같은 응답에
항상 같은 점수가 나와 개선 효과를 증명할 수 있다. 판단이 필요한 축(사실 충실도·환각)은
`judge.py` 가 맡는다.

이슈의 전제(답변에서 인용을 파싱한다)를 왜 따르지 않는가
--------------------------------------------------------
#624 는 "답변이 인용한 source id 와 `expected_source_ids` 대조"라고 적었다. 코드를 읽으면
그 전제가 성립하지 않는다.

- `[출처 N - {source_type}#{source_id}]` 형식은 모델에게 **넣어주는 컨텍스트**에만 있다
  (`generation_service._build_context`). 답변에 출처를 밝히라는 지시는 `_SYSTEM_PROMPT`
  어디에도 없다. 오히려 "마크다운 없이 일반 텍스트로", "대괄호·백틱·링크 문법을 쓰지
  마세요"라고 못 박고 예시 출력에도 출처 표기가 없다.
- 시스템 프롬프트가 "출처 머리말의 대괄호"를 언급하는 것은 모델이 컨텍스트를 **읽을 때**
  무엇을 믿을지 정하는 규칙이지, 답변에 그 표기를 쓰라는 지시가 아니다.
- `chat_service` 도 답변문을 파싱하지 않는다. `RagQueryResponse.sources` 는 검색 결과
  행(`rows`)에서 곧장 만들어진다.

그래서 답변 텍스트에서 source id 를 긁는 채점기는 늘 빈 집합을 얻는다. 전 케이스가 0점이
되거나, 인용이 있는 척 꾸민 가짜 답변으로만 통과하는 - 방어선이 있는 척하는 - 테스트가 된다.

대신 채점 입력을 **그 응답이 함께 돌려준 출처 목록**(`RagQueryResponse.sources` 의
`{source_type}#{source_id}` 집합)으로 잡는다. 이건 "답이 출처를 인용했는가"가 아니라 **그
사실을 뒷받침하는 출처가 실제로 답변 생성에 올라왔는가**를 재는 것이다. 근거 있는 답의
필요조건이고, 인용을 요구하지 않는 이 파이프라인에서 기계로 잴 수 있는 것의 상한이다.
심사기가 "답에 그 사실이 담겼는가"를 따로 재므로, 두 축을 나란히 놓으면 "사실이 담겼고 그
근거가 실제로 있었다"가 된다.

인용을 요구하도록 `_SYSTEM_PROMPT` 를 고치는 것은 운영 답변 형식이 바뀌는 일이라 별도
이슈다. 그 이슈가 반영되면 여기에 답변 파싱 축을 더할 수 있다.

채점 단위는 답변이 아니라 사실 하나다
--------------------------------------
`expected_source_ids` 는 상한(무엇이 근거로 인정되는가)만 정하는 화이트리스트다. 케이스
단위로 "화이트리스트 안의 출처가 하나라도 올라왔는가"만 보면, 사실이 여러 출처에 흩어진
케이스에서 출처 하나만 올라와도 통과한다. 나머지 사실은 근거가 없었던 셈인데 그걸 못 잡는다.

그래서 사실마다 `fact_evidence_sources()` 로 그 사실의 `evidence_snippet` 을 품은 출처
집합을 구하고, 검색 출처가 그 집합과 겹칠 때만 그 사실을 "근거 있음"으로 센다. 같은 내용이
여러 벌 적재된 중복 출처는 "같은 사실을 품은 출처가 여럿"이라는 뜻이라 이 규칙에 그대로
흡수되고, 사실이 흩어진 케이스는 출처 하나만 올라오면 나머지 사실에서 점수를 잃는다. 설계
근거 전문은 `test_dataset.py` 모듈 docstring 에 있다.

화이트리스트 밖 출처는 점수식에 넣지 않는다. 그런 출처만 올라온 응답은 어느 사실의 정답
집합과도 겹치지 않아 이미 0점이므로, 감점을 한 번 더 얹으면 같은 실패를 두 번 세는 것이
된다. 대신 진단용으로 `off_whitelist_sources` 에 남긴다.

이 축과 충실도 축은 여기서 합치지 않는다. 실패 방향이 다른 값을 하나로 뭉개면 서로를
가려준다는 것은 이 저장소가 회의록 평가에서 이미 비싸게 배웠다
(`meeting_eval/summary_judge` docstring). 두 축을 어떻게 볼지는 보고서를 만드는 쪽이 정한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from tests.assistant_eval.test_dataset import fact_evidence_sources


@dataclass(frozen=True)
class GroundingScore:
    score: float
    grounded_fact_ids: List[str]
    ungrounded_fact_ids: List[str]
    retrieved_sources: List[str]
    # 화이트리스트 밖에서 올라온 출처. 점수에는 넣지 않고 진단용으로만 남긴다.
    off_whitelist_sources: List[str] = field(default_factory=list)


def score_grounding(raw: Dict, retrieved_source_ids: Iterable[str]) -> GroundingScore:
    """케이스 하나의 근거 점수. 뒷받침 출처가 실제로 올라온 사실의 비율이다.

    `retrieved_source_ids` 는 그 답과 함께 돌아온 출처들의 `{source_type}#{source_id}` 다.
    """
    retrieved = set(retrieved_source_ids)
    whitelist = set(raw["expected_source_ids"])

    grounded: List[str] = []
    ungrounded: List[str] = []
    for fact in raw["must_include_facts"]:
        evidence = fact_evidence_sources(raw, fact)
        (grounded if retrieved & evidence else ungrounded).append(fact["fact_id"])

    total = len(grounded) + len(ungrounded)
    # 사실이 없는 케이스는 픽스처 검증이 막는다. 그래도 0으로 나누지 않도록 여기서 끊는데,
    # 잰 것이 없으면 점수를 줄 근거도 없으므로 0.0 이다(만점이 아니다).
    score = len(grounded) / total if total else 0.0

    return GroundingScore(
        score=score,
        grounded_fact_ids=grounded,
        ungrounded_fact_ids=ungrounded,
        retrieved_sources=sorted(retrieved),
        off_whitelist_sources=sorted(retrieved - whitelist),
    )
