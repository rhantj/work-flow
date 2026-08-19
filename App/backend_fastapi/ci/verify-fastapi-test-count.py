#!/usr/bin/env python3
"""FastAPI 테스트가 기대한 만큼 실제로 실행됐는지 확인한다.

pytest 는 --ignore 를 하나 더 붙이거나 파일이 통째로 수집되지 않아도 "통과"로 끝난다.
그러면 CI 는 초록불인데 실제로는 아무것도 안 지키는 상태가 된다 - 방어선이 있는 척하는
쪽이 없는 것보다 나쁘다. 그래서 실행 건수의 하한을 못 박는다.

테스트를 늘렸으면 MINIMUM_TESTS 도 같이 올린다. 줄이려면 왜 줄이는지 이유를 남긴다.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# 2026-08-02 기준 실행 건수는 670이다.
#
#   404  tests/llm_rag_assistant (통합 5건 포함 - 큐 누수를 고쳐 --ignore 를 걷어냈다)
#   234  그 밖의 tests/ (CI 범위를 tests 전체로 넓히기 전에는 아무도 안 보던 것들)
#     3  로깅 설정 테스트
#    29  질의 집계 카운터 (필드 조건 17 + 검색 경로 배선 7 + 읽기 스크립트 5)
#
# 여유를 두지 않고 실제 건수에 맞춘다. 통합 5건은 Docker 가 없으면 스킵되는데, 여유를 두면
# 그 스킵이 그대로 통과해 pgvector 커버리지가 소리 없이 사라진다 - 이 스크립트가 막으려는
# 상황 그 자체다. ubuntu-latest 에는 Docker 가 있으므로 스킵되면 그게 이상 신호다.
#
# 여기 걸리면 숫자부터 낮추지 말고 왜 줄었는지 먼저 확인한다. 테스트를 늘렸으면 같이 올린다.
#
# 2026-08-04: 728 -> 733. 담당자 사실 조회 5건(조회 3 + 출처 줄 표기 2)을 더했다.
# 2026-08-04: 733 -> 738. 질문이 지목한 출처 표시 5건을 더했다.
# 2026-08-04: 738 -> 747. 실행항목 칸의 담당자 자리 제거 9건을 더했다.
# 2026-08-04: 747 -> 757. 담당자 후보 승격 5건 + 기한 자리 제거 5건을 더했다.
# 2026-08-04: 757 -> 762. 기한 칸 날짜 인정 5건을 더했다.
# 2026-08-18: 762 -> 766. 생성기가 어느 백엔드로 답했는지 돌려주는 4건.
# 2026-08-18: 766 -> 770. 응답에 provider 를 싣고 캐시 스키마를 v16 으로 올리는 4건.
#             (위 두 줄은 그때 이 목록에 적지 않은 것을 2026-08-19 에 채워 넣었다.)
#
# 2026-08-19: 770 -> 878. 실측에 맞춰 정산한다.
#             38건은 이번에 더한 것이다 - provider 전파 3, 프로바이더 집계 12,
#             답변 평가셋 픽스처 23. 나머지 70건은 그 전부터 쌓여 있던 드리프트다.
#
#             하한이 실측보다 70건 낮다는 것은 그만큼의 테스트가 통째로 수집되지 않아도
#             CI 가 초록으로 끝난다는 뜻이다. 이 스크립트가 막으려던 상황 그 자체가
#             스크립트 안에서 벌어지고 있었다.
#
#             정산을 지금 하는 이유: 이슈 넷을 병렬로 진행하면 네 브랜치가 이 한 줄을
#             각자 다른 숫자로 고쳐 전부 충돌한다. 하한이라 올리지 않아도 CI 는 통과하므로
#             일부러 미뤘고, 넷이 전부 병합된 뒤 한 번에 올린다.
# 2026-08-19: 878 -> 877. 검색 평가셋 원본을 추적하면서 그 대체물이던 파생 인덱스와
#             인덱스 형태 검사 1건을 지웠다. 대조 상대가 사본에서 원본으로 바뀌어
#             검증은 오히려 강해졌다.
# 2026-08-19: 877 -> 932. 두 이슈를 병렬로 진행하고 병합한 뒤 한 번에 정산한다.
#             47건은 어시스턴트 답변 채점기·심사기(#624), 8건은 캐시 히트 집계(#635)다.
#
#             이번에도 두 브랜치 모두 이 줄을 건드리지 않게 했다. 하한이라 올리지 않아도
#             CI 는 통과하므로, 각자 다른 숫자로 고쳐 충돌하는 것보다 병합 후 실측이 낫다.
MINIMUM_TESTS = 932


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify-fastapi-test-count.py <junit-xml>", file=sys.stderr)
        return 2

    report = Path(sys.argv[1])
    if not report.is_file():
        print(f"[FAIL] JUnit 리포트가 없습니다: {report}", file=sys.stderr)
        print("       pytest 가 실행 자체를 못 했다는 뜻이므로 통과시키지 않는다.", file=sys.stderr)
        return 1

    root = ET.parse(report).getroot()
    # pytest 는 <testsuites><testsuite>...로 감싸기도 하고 <testsuite> 단독이기도 하다.
    suites = root.findall("testsuite") if root.tag == "testsuites" else [root]

    total = skipped = failures = errors = 0
    for suite in suites:
        total += int(suite.get("tests", 0))
        skipped += int(suite.get("skipped", 0))
        failures += int(suite.get("failures", 0))
        errors += int(suite.get("errors", 0))

    executed = total - skipped
    print(f"수집 {total}건 / 건너뜀 {skipped}건 / 실제 실행 {executed}건 "
          f"(실패 {failures}, 오류 {errors})")

    if executed < MINIMUM_TESTS:
        print(f"[FAIL] 실행된 테스트가 {executed}건으로 하한 {MINIMUM_TESTS}건에 못 미칩니다.",
              file=sys.stderr)
        print("       테스트가 조용히 빠졌는지 확인하세요(--ignore 추가, 수집 실패, 건너뜀).",
              file=sys.stderr)
        print("       의도적으로 줄인 것이라면 이 스크립트의 MINIMUM_TESTS 를 이유와 함께 낮추세요.",
              file=sys.stderr)
        return 1

    print(f"[OK] 하한 {MINIMUM_TESTS}건을 넘겼습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
