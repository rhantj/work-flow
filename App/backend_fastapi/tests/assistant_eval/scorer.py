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
집합을 구하고, 검색 출처가 그 집합과 겹칠 때만 그 사실을 "근거 있음"으로 센다. 사실이
흩어진 케이스는 출처 하나만 올라오면 나머지 사실에서 점수를 잃는다. 설계 근거 전문은
`test_dataset.py` 모듈 docstring 에 있다.

**정정 (2026-08-20).** 이 자리에 원래 "같은 내용이 여러 벌 적재된 중복 출처는 이 규칙에
그대로 흡수된다"고 적었는데 사실이 아니었다. `fact_evidence_sources()` 는
`expected_source_excerpts` **안에서만** 찾으므로, 화이트리스트 밖의 쌍둥이는 후보에
들어오지도 않는다. 운영 데이터에 그런 쌍둥이가 실제로 있다 - 프로젝트 1의 청크 308건 중
내용 중복 잉여 75건, 픽스처 30건 중 7건이 화이트리스트 밖 쌍둥이 보유.

그래서 `retrieved_contents` 를 받으면 본문 대조를 합집합으로 더한다. 실측 영향은
`semantic` +0.033, 전체 +0.011 로 작았고 점수가 달라진 케이스는 `semantic-09` 하나다
(검색기가 화이트리스트의 `task#77` 대신 같은 문장을 담은 `task#35` 를 올렸다). 쌍둥이가
있어도 검색기가 그것을 실제로 올려야 차이가 나기 때문이다. **즉 semantic 0.40 의 대부분은
채점 결함이 아니라 진짜 검색 실패다.** 이 구분을 못 하면 자를 고쳐놓고 검색이 좋아졌다고
읽게 된다.

화이트리스트 밖 출처는 점수식에 넣지 않는다. 그런 출처만 올라온 응답은 어느 사실의 정답
집합과도 겹치지 않아 이미 0점이므로, 감점을 한 번 더 얹으면 같은 실패를 두 번 세는 것이
된다. 대신 진단용으로 `off_whitelist_sources` 에 남긴다.

이 축과 충실도 축은 여기서 합치지 않는다. 실패 방향이 다른 값을 하나로 뭉개면 서로를
가려준다는 것은 이 저장소가 회의록 평가에서 이미 비싸게 배웠다
(`meeting_eval/summary_judge` docstring). 두 축을 어떻게 볼지는 보고서를 만드는 쪽이 정한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional

from tests.assistant_eval.test_dataset import fact_evidence_sources, squeeze


@dataclass(frozen=True)
class GroundingScore:
    score: float
    # frozen 이어도 List 를 담으면 안이 바뀐다. 채점 결과가 소비자 쪽에서 조용히 달라지면
    # 재현이 안 되므로 tuple 로 못 박는다.
    grounded_fact_ids: tuple[str, ...]
    ungrounded_fact_ids: tuple[str, ...]
    retrieved_sources: tuple[str, ...]
    # 화이트리스트 밖에서 올라온 출처. 점수에는 넣지 않고 진단용으로만 남긴다.
    off_whitelist_sources: tuple[str, ...] = ()
    # id 로는 못 잡고 본문 대조로만 잡힌 사실. 옛 id 전용 채점이 얼마나 낮게 쟀는지가
    # 이 값이다. 점수가 올라갔을 때 검색이 좋아진 것인지 채점이 느슨해진 것인지를
    # 이걸 봐야 가른다.
    content_only_fact_ids: tuple[str, ...] = ()


def score_grounding(
    raw: Dict,
    retrieved_source_ids: Iterable[str],
    retrieved_contents: Optional[Mapping[str, str]] = None,
) -> GroundingScore:
    """케이스 하나의 근거 점수. 뒷받침 출처가 실제로 올라온 사실의 비율이다.

    `retrieved_source_ids` 는 그 답과 함께 돌아온 출처들의 `{source_type}#{source_id}` 다.

    `retrieved_contents` 를 주면 id 대조에 본문 대조를 더한다(합집합). 같은 내용이 다른
    id 로 여러 벌 적재돼 있으면 id 만으로는 근거를 놓친다 - 검색기가 그 사실을 글자 그대로
    담은 청크를 올렸는데도 화이트리스트에 그 id 가 없다는 이유로 0점이 나가고, 그러면 재는
    것이 검색 품질이 아니라 화이트리스트의 넓이가 된다. 운영 데이터에서 실제로 그랬다
    (프로젝트 1: 청크 308건 중 내용 중복 잉여 75건, 픽스처 30건 중 7건이 화이트리스트 밖
    쌍둥이 보유).

    합집합인 이유: 본문 대조는 순수하게 증거를 더하는 것이라 기존 판정을 뒤집지 않는다.
    안 주면 예전과 똑같이 동작한다 - 기존 호출부가 조용히 달라지지 않게 하기 위해서다.
    """
    retrieved = set(retrieved_source_ids)
    whitelist = set(raw["expected_source_ids"])
    contents = dict(retrieved_contents or {})
    squeezed_contents = [squeeze(text) for text in contents.values()]

    grounded: List[str] = []
    ungrounded: List[str] = []
    content_only: List[str] = []
    for fact in raw["must_include_facts"]:
        evidence = fact_evidence_sources(raw, fact)
        by_id = bool(retrieved & evidence)
        # 조각이 빈 사실은 아무 본문에나 걸리므로 본문 대조에서 뺀다. 안 그러면 근거가
        # 없는데도 전부 통과해 채점기가 통째로 무의미해진다.
        snippet = squeeze(fact["evidence_snippet"])
        by_content = bool(snippet) and any(snippet in text for text in squeezed_contents)
        if by_id or by_content:
            grounded.append(fact["fact_id"])
            if not by_id:
                content_only.append(fact["fact_id"])
        else:
            ungrounded.append(fact["fact_id"])

    total = len(grounded) + len(ungrounded)
    # 사실이 없는 케이스는 픽스처 검증이 막는다. 그래도 0으로 나누지 않도록 여기서 끊는데,
    # 잰 것이 없으면 점수를 줄 근거도 없으므로 0.0 이다(만점이 아니다).
    score = len(grounded) / total if total else 0.0

    return GroundingScore(
        score=score,
        grounded_fact_ids=tuple(grounded),
        ungrounded_fact_ids=tuple(ungrounded),
        retrieved_sources=tuple(sorted(retrieved)),
        off_whitelist_sources=tuple(sorted(retrieved - whitelist)),
        content_only_fact_ids=tuple(content_only),
    )
