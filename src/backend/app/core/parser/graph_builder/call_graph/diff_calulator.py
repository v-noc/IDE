from __future__ import annotations

import uuid
from typing import Dict, Iterable, List, Set

from app.core.model.nodes import CallNode
from app.core.model.schemas.code_element_schema import CallSchema
from app.core.parser.jedi_adapter.call_resolver.call_resolver import CallFrameStack
from app.core.schemas.tree import AnyTreeNode
from .models import ScopeSyncResult


class DiffCalculator:
    """Calculate full tree diff and return one batch ScopeSyncResult."""

    def calculate_diff(
        self,
        *,
        root_parent_id: str,
        new_tree: CallFrameStack,
        old_tree: List[AnyTreeNode],
    ) -> ScopeSyncResult:
        aggregate = ScopeSyncResult(
            parent_id=root_parent_id,
            added_target_ids=set(),
            retained_target_ids=set(),
            removed_target_ids=set(),
            created_map={},
            calls_to_create=[],
            moves_to_execute=[],
            call_ids_to_remove=[],
        )
        root_map = self._walk(
            parent_id=root_parent_id,
            new_children=new_tree.children,
            old_children=old_tree,
            aggregate=aggregate,
        )
        aggregate.created_map = root_map
        return aggregate

    def _walk(
        self,
        *,
        parent_id: str,
        new_children: Iterable[CallFrameStack],
        old_children: List[AnyTreeNode],
        aggregate: ScopeSyncResult,
    ) -> Dict[str, str]:
        old_target_to_call = self._map_old_calls_by_target(old_children)
        new_target_to_call = {
            child.target_id: child for child in new_children if child.target_id
        }

        old_targets = set(old_target_to_call.keys())
        new_targets = set(new_target_to_call.keys())

        added = new_targets - old_targets
        retained = new_targets & old_targets
        removed = old_targets - new_targets

        calls_to_create: List[CallNode] = []
        moves_to_execute = []
        call_ids_to_remove = [old_target_to_call[tid].id for tid in removed]

        active_call_map: Dict[str, str] = {
            target_id: old_target_to_call[target_id].id for target_id in retained
        }

        for target_id in added:
            new_call = new_target_to_call[target_id]
            call_name = new_call.target_qname.split(
                ".")[-1] if new_call.target_qname else target_id
            created_node = CallNode(
                id=f"{CallSchema.__name__}/{str(uuid.uuid4())}",
                qname=f"{parent_id}::{target_id}",
                name=call_name,
                target_function=target_id,
                description=f"call::{new_call.target_qname}",
            )
            calls_to_create.append(created_node)
            moves_to_execute.append((created_node.id, parent_id, "call"))
            active_call_map[target_id] = created_node.id

        aggregate.added_target_ids.update(added)
        aggregate.retained_target_ids.update(retained)
        aggregate.removed_target_ids.update(removed)
        aggregate.calls_to_create.extend(calls_to_create)
        aggregate.moves_to_execute.extend(moves_to_execute)
        aggregate.call_ids_to_remove.extend(call_ids_to_remove)

        for target_id in new_targets:
            new_call_node = new_target_to_call[target_id]
            next_parent_id = active_call_map[target_id]
            next_old_children = []
            if target_id in retained:
                old_call_node = old_target_to_call[target_id]
                next_old_children = getattr(old_call_node, "children", [])
            self._walk(
                parent_id=next_parent_id,
                new_children=new_call_node.children,
                old_children=next_old_children,
                aggregate=aggregate,
            )
        return active_call_map

    def _map_old_calls_by_target(
        self, old_children: List[AnyTreeNode]
    ) -> Dict[str, AnyTreeNode]:
        call_nodes = self._flatten_calls_skipping_groups(old_children)
        result: Dict[str, AnyTreeNode] = {}
        for call_node in call_nodes:
            target_id = self._old_call_target_id(call_node)
            if target_id and target_id not in result:
                result[target_id] = call_node
        return result

    def _flatten_calls_skipping_groups(
        self, nodes: List[AnyTreeNode]
    ) -> List[AnyTreeNode]:
        result: List[AnyTreeNode] = []
        stack = list(nodes)
        while stack:
            node = stack.pop(0)
            if self._is_group_node(node):
                stack = list(getattr(node, "children", [])) + stack
                continue
            if self._is_call_node(node):
                result.append(node)
        return result

    @staticmethod
    def _is_group_node(node: AnyTreeNode) -> bool:
        return getattr(node, "node_type", None) == "group"

    @staticmethod
    def _is_call_node(node: AnyTreeNode) -> bool:
        return getattr(node, "node_type", None) == "call"

    @staticmethod
    def _old_call_target_id(call_node: AnyTreeNode) -> str | None:
        target_function = getattr(call_node, "target_function", None)
        if isinstance(target_function, str) and target_function:
            return target_function

        target = getattr(call_node, "target", None)
        target_id = getattr(target, "id", None) if target else None
        if isinstance(target_id, str) and target_id:
            return target_id
        return None
