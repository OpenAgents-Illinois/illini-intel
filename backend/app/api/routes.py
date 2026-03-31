from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse, StreamingResponse

from app.core.config import DEFAULT_GOAL
from app.models import events
from app.services.pipeline import run as run_pipeline

router = APIRouter()
logger = logging.getLogger("illini_intel")


@router.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    return "ok"


@router.get("/analyze")
async def analyze(goal: str = Query(default=DEFAULT_GOAL)) -> StreamingResponse:
    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    def emit(event: dict[str, Any]) -> None:
        queue.put_nowait(event)

    async def runner() -> None:
        try:
            await asyncio.to_thread(run_pipeline, goal, emit)
        except Exception as error:
            logger.exception("pipeline failed")
            queue.put_nowait(events.agent_thought("server", f"Server error: {error!r}"))
            queue.put_nowait(events.done())

    asyncio.create_task(runner())

    async def event_stream():
        while True:
            item = await queue.get()
            yield f"data: {json.dumps(item, default=str)}\n\n"
            if item.get("type") == "done":
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
