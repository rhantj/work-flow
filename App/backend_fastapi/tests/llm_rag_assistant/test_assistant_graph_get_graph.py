from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from llm_rag_assistant.app.graph import assistant_graph


@pytest.mark.asyncio
async def test_get_graph_builds_once_under_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    """최초 동시 요청이 몰려도 그래프는 한 번만 컴파일된다(중복 생성 방지)."""
    monkeypatch.setattr(assistant_graph, "_compiled", None)
    monkeypatch.setattr(assistant_graph, "_graph_lock", asyncio.Lock())

    compiled_sentinel = object()
    builder = MagicMock()

    def _compile(*args: object, **kwargs: object) -> object:
        # 컨텍스트 스위치를 강제해 잠금이 없으면 경쟁이 드러나게 한다.
        return compiled_sentinel

    builder.compile = MagicMock(side_effect=_compile)

    # _build는 동기 함수라 그대로 두고, 경쟁 노출은 compile 호출 카운트로 검증한다.
    with patch.object(assistant_graph, "_build", MagicMock(return_value=builder)):
        results = await asyncio.gather(
            *[assistant_graph.get_graph() for _ in range(10)]
        )

    assert all(result is compiled_sentinel for result in results)
    assert builder.compile.call_count == 1


@pytest.mark.asyncio
async def test_close_graph_resets_compiled(monkeypatch: pytest.MonkeyPatch) -> None:
    """종료 시 전역 그래프 상태를 초기화한다(InMemorySaver는 닫을 자원이 없다)."""
    monkeypatch.setattr(assistant_graph, "_compiled", object())
    monkeypatch.setattr(assistant_graph, "_graph_lock", asyncio.Lock())

    await assistant_graph.close_graph()

    assert assistant_graph._compiled is None
