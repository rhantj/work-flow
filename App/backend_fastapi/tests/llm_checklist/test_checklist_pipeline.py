from __future__ import annotations

import pytest

from llm_checklist.app.checklist_pipeline import (
    build_checklist_prompt,
    generate_checklist_minimal_fallback,
    parse_checklist_response,
)
from llm_checklist.app.checklist_schema import ChecklistGenerateRequest


def test_parse_valid_json_returns_suggestions():
    raw = '{"items": [{"title": "API 설계", "reason": "기반"}, {"title": "단위 테스트 작성", "reason": ""}]}'
    items = parse_checklist_response(raw)
    assert [i.title for i in items] == ["API 설계", "단위 테스트 작성"]
    assert items[0].reason == "기반"


def test_parse_strips_code_fence():
    items = parse_checklist_response('```json\n{"items": [{"title": "구현"}]}\n```')
    assert items[0].title == "구현"


def test_parse_broken_json_raises():
    with pytest.raises(Exception):
        parse_checklist_response("not json")


def test_parse_empty_items_raises():
    with pytest.raises(ValueError):
        parse_checklist_response('{"items": []}')


def test_minimal_fallback_marks_rule_based_and_skips_existing():
    req = ChecklistGenerateRequest(title="로그인 API", category="backend", existing_items=["요구사항 확인"])
    res = generate_checklist_minimal_fallback(req)
    titles = [i.title for i in res.items]
    assert res.engine == "rule-based"
    assert "요구사항 확인" not in titles
    assert res.items


def test_build_prompt_includes_task_fields_and_existing():
    req = ChecklistGenerateRequest(title="로그인 구현", category="backend", existing_items=["API 설계"])
    prompt = build_checklist_prompt(req)
    assert "로그인 구현" in prompt and "backend" in prompt and "API 설계" in prompt
