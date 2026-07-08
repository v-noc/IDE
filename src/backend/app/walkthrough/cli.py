"""CLI harness: uv run python -m app.walkthrough.cli <project_id> <node_id> <depth>"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from app.db.async_terminus_client import AsyncClient
from app.db.context import ProjectUoW, RequestDbContext
from app.walkthrough.service import WalkthroughService
from app.walkthrough.schemas import RunRequest
from app.core.services.code_element_service import CodeElementService
from app.core.services.project_service import ProjectService
from app.config.settings import get_settings


async def _main() -> int:
    parser = argparse.ArgumentParser(description="Run walkthrough estimate or stream")
    parser.add_argument("project_id")
    parser.add_argument("node_id")
    parser.add_argument("depth", type=int)
    parser.add_argument("--estimate-only", action="store_true")
    args = parser.parse_args()

    settings = get_settings()
    client = AsyncClient(
        settings.TERMINUS_HOST,
        settings.TERMINUS_USER,
        settings.TERMINUS_KEY,
        team=settings.TERMINUS_TEAM,
        db=settings.TERMINUS_DB,
    )
    project_service = ProjectService(ProjectUoW(client, None, RequestDbContext()))
    project = await project_service.get(args.project_id)
    if not project:
        print("Project not found", file=sys.stderr)
        return 1

    from app.core.model.nodes import ProjectNode

    uow = ProjectUoW(client, ProjectNode.from_raw_dict(project), RequestDbContext())
    service = WalkthroughService(uow)
    code_service = CodeElementService(uow)

    if args.estimate_only:
        result = await service.estimate(args.node_id, args.depth)
        print(json.dumps(result.model_dump(), indent=2))
        return 0

    request = RunRequest(
        project_id=args.project_id,
        node_id=args.node_id,
        depth=args.depth,
    )
    async for frame in service._stream_run(request, code_service):
        print(json.dumps(frame))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
