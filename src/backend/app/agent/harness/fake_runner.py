from __future__ import annotations

import asyncio
import re

import time

from app.agent.harness.echo_runner import run_echo
from app.agent.harness.history import latest_node_refs
from app.agent.harness.middleware import build_attached_blocks
from app.agent.harness.patcher import ConversationPatcher
from app.agent.prompts.registry import get_prompt_registry
from app.agent.schemas.conversation import (
    Conversation,
    EffortLevel,
    MessageMetadata,
    TokenUsage,
)
from app.agent.schemas.parts import TextPart
from app.core.services.code_element_service import CodeElementService
from app.db.context import ProjectUoW


def _extract_name_from_block(block: str) -> str | None:
    match = re.search(r'name="([^"]+)"', block)
    return match.group(1) if match else None


def _extract_description(block: str) -> str | None:
    match = re.search(
        r"<description>(.*?)</description>",
        block,
        flags=re.DOTALL,
    )
    if not match:
        return None
    return match.group(1).strip()


async def run_fake_enriched(
    patcher: ConversationPatcher,
    *,
    conversation: Conversation,
    assistant_index: int,
    uow: ProjectUoW,
    effort: EffortLevel | None = None,
    cancelled: asyncio.Event | None = None,
    chunk_delay_s: float = 0.01,
) -> MessageMetadata:
    """Offline Phase-2 stand-in: answer from attached_node enrichment."""
    repos = uow.get_project_repos()
    code_service = CodeElementService(uow)

    async def code_loader(node_id: str) -> str | None:
        try:
            result = await code_service.get_code(node_id)
        except Exception:
            return None
        if not result:
            return None
        return result.get("code") or result.get("content")

    node_refs = latest_node_refs(conversation)
    try:
        attached = await build_attached_blocks(
            repos,
            node_refs,
            code_loader=code_loader,
        )
    except Exception:
        attached = {}

    if attached:
        lines: list[str] = []
        for node_id, block in attached.items():
            name = _extract_name_from_block(block) or node_id
            desc = _extract_description(block)
            if desc:
                lines.append(f"`{name}` — {desc}")
            else:
                lines.append(f"`{name}` is attached in this turn.")
        reply = "From the attached context: " + " ".join(lines)
    else:
        # Fall back to plain echo when nothing is attached
        user_text = ""
        for message in reversed(conversation.messages):
            if message.role != "user":
                continue
            for part in message.parts:
                if isinstance(part, TextPart):
                    user_text = part.text
                    break
            break
        return await run_echo(
            patcher,
            assistant_index=assistant_index,
            user_text=user_text,
            cancelled=cancelled,
            chunk_delay_s=chunk_delay_s,
        )

    started = time.monotonic()
    prompt_version = get_prompt_registry().version("agent.system")
    part_index = await patcher.add_part(assistant_index, TextPart(text=""))
    chunk_size = max(1, len(reply) // 6) if len(reply) > 6 else 1
    for start in range(0, len(reply), chunk_size):
        if cancelled is not None and cancelled.is_set():
            return MessageMetadata(
                model_id="fake:echo",
                prompt_version=prompt_version,
                effort=effort,
                usage=TokenUsage(),
                duration_ms=int((time.monotonic() - started) * 1000),
                stop_reason="cancelled",
            )
        await patcher.append_text(
            assistant_index,
            part_index,
            reply[start : start + chunk_size],
        )
        if chunk_delay_s > 0:
            await asyncio.sleep(chunk_delay_s)

    return MessageMetadata(
        model_id="fake:echo",
        prompt_version=prompt_version,
        effort=effort,
        usage=TokenUsage(),
        duration_ms=int((time.monotonic() - started) * 1000),
        stop_reason="end_turn",
    )
