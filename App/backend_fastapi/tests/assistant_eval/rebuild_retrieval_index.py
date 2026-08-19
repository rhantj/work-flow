#!/usr/bin/env python3
"""검색 평가셋 원본에서 추적되는 대조 인덱스를 다시 만든다.

`tests/fixtures/assistant_eval_retrieval_index.json` 은 검색 평가셋
`output/hybrid_rag_eval/data/evalset.json` 에서 세 필드(id, category, question)만 추린
사본이다. 원본은 `output/` 아래라 git 미추적이고 CI 에는 없다(테스트 모듈 docstring 참고).

사본을 손으로 추리면 그 추림 자체가 검증되지 않는다. 여기 규칙을 한 곳에 두고,
평가셋을 다시 만들었을 때는 이 스크립트로 다시 써서 diff 를 리뷰에 올린다.

    python tests/assistant_eval/rebuild_retrieval_index.py \\
        ../../output/hybrid_rag_eval/data/evalset.json

`canonical_index` / `dumps` 는 테스트도 함께 쓴다. 커밋된 인덱스가 이 함수들이 내는 모양과
글자까지 같은지 CI 가 확인하므로, 원본 없이 손으로 고친 흔적은 원본이 없어도 드러난다.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List

SOURCE = "output/hybrid_rag_eval/data/evalset.json"
FIELDS = ("id", "category", "question")
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
INDEX_PATH = FIXTURES / "assistant_eval_retrieval_index.json"


def canonical_index(cases: List[Dict]) -> Dict:
    """평가셋 케이스 목록에서 대조에 필요한 세 필드만 id 순으로 추린다."""
    return {
        "source": SOURCE,
        "fields": list(FIELDS),
        "cases": [
            {field: case[field] for field in FIELDS}
            for case in sorted(cases, key=lambda case: case["id"])
        ],
    }


def dumps(index: Dict) -> str:
    return json.dumps(index, ensure_ascii=False, indent=2) + "\n"


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <evalset.json>", file=sys.stderr)
        return 2

    cases = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    INDEX_PATH.write_text(dumps(canonical_index(cases)), encoding="utf-8")
    print(f"{INDEX_PATH} 에 {len(cases)}건을 다시 썼습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
