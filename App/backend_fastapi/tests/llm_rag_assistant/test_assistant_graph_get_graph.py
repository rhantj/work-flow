from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from llm_rag_assistant.app.graph import assistant_graph


@pytest.mark.asyncio
async def test_get_graph_builds_once_under_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    """최초 동시 요청이 몰려도 체크포인터는 한 번만 만들어진다(Redis 연결 누수 방지)."""
    monkeypatch.setattr(assistant_graph, "_compiled", None)
    monkeypatch.setattr(assistant_graph, "_checkpointer_cm", None)
    monkeypatch.setattr(assistant_graph, "_graph_lock", asyncio.Lock())

    checkpointer = MagicMock()

    async def _asetup() -> None:
        await asyncio.sleep(0)  # 컨텍스트 스위치를 강제해 잠금이 없으면 경쟁이 드러나게 한다.

    checkpointer.asetup = _asetup

    cm = MagicMock()

    async def _aenter(*args: object) -> MagicMock:
        await asyncio.sleep(0)
        return checkpointer

    cm.__aenter__ = _aenter

    from_conn = MagicMock(return_value=cm)
    saver_cls = MagicMock()
    saver_cls.from_conn_string = from_conn

    compiled_sentinel = object()
    builder = MagicMock()
    builder.compile = MagicMock(return_value=compiled_sentinel)

    with patch.object(assistant_graph, "AsyncRedisSaver", saver_cls), patch.object(
        assistant_graph, "_build", MagicMock(return_value=builder)
    ), patch.object(
        assistant_graph, "get_settings", MagicMock(return_value=MagicMock(redis_url="redis://x"))
    ):
        results = await asyncio.gather(
            *[assistant_graph.get_graph() for _ in range(10)]
        )

    assert all(result is compiled_sentinel for result in results)
    assert from_conn.call_count == 1
    assert builder.compile.call_count == 1
