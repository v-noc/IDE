"""
Topological insert order for CallNode batches.

Placed under app.core to avoid importing graph_builder from services.
"""

from __future__ import annotations

import logging
from collections import defaultdict, deque
from typing import Deque, Dict, List, Set

from app.core.model.nodes import CallNode

logger = logging.getLogger(__name__)


def toposort_calls_for_insert(calls: List[CallNode]) -> List[CallNode]:
    """
    Order calls so each child id appears before any new parent document that
    lists it under call_children. If a cycle is detected, log and return the
    original order.
    """
    if len(calls) <= 1:
        return list(calls)

    insert_ids: Set[str] = {n.id for n in calls}
    id_to_node: Dict[str, CallNode] = {n.id: n for n in calls}
    graph: Dict[str, List[str]] = defaultdict(list)
    in_degree: Dict[str, int] = {n.id: 0 for n in calls}

    for parent in calls:
        call_children = parent.get_children_by_type().get(
            "call_children", set()
        )
        for cid in call_children & insert_ids:
            graph[cid].append(parent.id)
            in_degree[parent.id] += 1

    queue: Deque[str] = deque(
        nid for nid, deg in in_degree.items() if deg == 0
    )
    ordered_ids: List[str] = []
    while queue:
        nid = queue.popleft()
        ordered_ids.append(nid)
        for succ in graph[nid]:
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)

    if len(ordered_ids) != len(calls):
        logger.warning(
            "Call insert toposort: cycle or missing node; using input order"
        )
        return list(calls)

    return [id_to_node[nid] for nid in ordered_ids]
