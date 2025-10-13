import re
from typing import Dict, List

from ast import parse, walk, Expr, Call, Name, FunctionDef, ClassDef
from .metadata import (
    build_comment_map,
    resolve_metadata_for_line,
    add_comment as add_docstring_comment,
)

METADATA_REGEX = re.compile(r"(\w+):\s*([^,]+)")


"""Thin metadata accessors, delegating to metadata helpers."""


def get_call_metadata(source: str) -> List[Dict[str, object]]:
    try:
        tree = parse(source)
    except Exception:
        return []
    comment_map = build_comment_map(tree)
    lines = source.splitlines()
    results: List[Dict[str, object]] = []
    for node in walk(tree):
        if isinstance(node, Expr) and isinstance(node.value, Call):
            call_node: Call = node.value
            metadata = resolve_metadata_for_line(
                comment_map, lines, call_node.lineno
            )
            if not metadata:
                continue
            func_name = ""
            if isinstance(call_node.func, Name):
                func_name = call_node.func.id
            results.append(
                {
                    "function_name": func_name,
                    "line": call_node.lineno,
                    "metadata": metadata,
                }
            )
    return results


def get_function_metadata(source: str) -> List[Dict[str, object]]:
    try:
        tree = parse(source)
    except Exception:
        return []
    comment_map = build_comment_map(tree)
    lines = source.splitlines()
    results: List[Dict[str, object]] = []
    for node in walk(tree):
        if isinstance(node, FunctionDef):
            metadata = resolve_metadata_for_line(
                comment_map, lines, node.lineno)
            if not metadata:
                continue
            results.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "metadata": metadata,
                }
            )
    return results


def get_class_metadata(source: str) -> List[Dict[str, object]]:
    try:
        tree = parse(source)
    except Exception:
        return []
    comment_map = build_comment_map(tree)
    lines = source.splitlines()
    results: List[Dict[str, object]] = []
    for node in walk(tree):
        if isinstance(node, ClassDef):
            metadata = resolve_metadata_for_line(
                comment_map, lines, node.lineno)
            if not metadata:
                continue
            results.append(
                {
                    "name": node.name,
                    "line": node.lineno,
                    "metadata": metadata,
                }
            )
    return results


def add_comment(
    filepath: str,
    target_name: str,
    comment_text: str,
) -> dict:
    """Write a one-line docstring ID for a specific def/class.

    target_name can be a dot-qualified path of any depth:
      - function_name (module-level)
      - ClassName
      - ClassName.method
      - ClassA.InnerB.method
      - outer_fn.inner_fn.deep_fn
    """
    try:
        with open(filepath, "r") as f:
            source = f.read()
    except Exception:
        return {"success": False, "added_lines": 0}

    try:
        tree = parse(source)
    except Exception:
        return {"success": False, "added_lines": 0}

    def _find_child_by_name(body_nodes, name):
        for child in body_nodes:
            if isinstance(child, (FunctionDef, ClassDef)) and getattr(
                child, "name", None
            ) == name:
                return child
        return None

    parts = target_name.split(".") if target_name else []
    current_node = tree
    target_node = None

    if parts:
        for i, segment in enumerate(parts):
            # For module-level items, search the tree body directly
            if i == 0:
                body = getattr(current_node, "body", [])
            else:
                body = getattr(target_node, "body", [])

            found = _find_child_by_name(body, segment)
            if not found:
                target_node = None
                break
            target_node = found

    line_number = getattr(target_node, "lineno", None) if target_node else None

    if line_number is None:
        return {"success": False, "added_lines": 0}

    return add_docstring_comment(
        filepath=filepath,
        comment_text=comment_text,
        line_number=line_number,
    )


def get_node_metadata(source: str):
    return {
        "calls": get_call_metadata(source),
        "functions": get_function_metadata(source),
        "classes": get_class_metadata(source),
    }
