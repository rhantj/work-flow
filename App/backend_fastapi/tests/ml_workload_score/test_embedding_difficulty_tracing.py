from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, patch

import pytest

from ml_workload_score.app.services import embedding_difficulty as mod


@pytest.mark.asyncio
async def test_embed_still_async_and_returns_embedding_after_traceable():
    assert inspect.iscoroutinefunction(mod._embed)

    fake_client = AsyncMock()
    fake_client.embeddings = AsyncMock(return_value={"embedding": [0.1, 0.2, 0.3]})

    with patch(
        "ml_workload_score.app.services.embedding_difficulty.ollama.AsyncClient",
        return_value=fake_client,
    ):
        result = await mod._embed("테스트 문장")

    assert result == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_get_anchor_embeddings_still_async_and_caches():
    mod._anchor_cache.clear()
    assert inspect.iscoroutinefunction(mod.get_anchor_embeddings)

    fake_client = AsyncMock()
    fake_client.embeddings = AsyncMock(return_value={"embedding": [1.0]})

    with patch(
        "ml_workload_score.app.services.embedding_difficulty.ollama.AsyncClient",
        return_value=fake_client,
    ):
        hard, easy = await mod.get_anchor_embeddings()

    assert hard == [1.0]
    assert easy == [1.0]
