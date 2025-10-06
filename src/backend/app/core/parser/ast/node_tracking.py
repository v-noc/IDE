import re
from typing import Dict, List

from .ast_comment import parse, walk, Expr, Call, Name, FunctionDef, ClassDef
from .metadata import (
    build_comment_map,
    resolve_metadata_for_line,
    parse_comment_data,
    format_dict_to_data,
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
    line_number: int,
    position: str = "inline",
) -> dict:
    if position not in ["inline", "above"]:
        return {"success": False, "added_lines": 0}
    try:
        with open(filepath, "r") as f:
            source = f.read()
    except Exception:
        return {"success": False, "added_lines": 0}
    try:
        parse(source)
    except Exception:
        return {"success": False, "added_lines": 0}
    lines = source.splitlines()
    idx = max(0, line_number - 1)
    new_data = parse_comment_data(comment_text)
    added_lines = 0
    if position == "inline":
        original_line = lines[idx] if idx < len(lines) else ""
        if "#" in original_line:
            code_part, comment_part = original_line.split("#", 1)
        else:
            code_part, comment_part = original_line, ""
        existing_data = (
            parse_comment_data(comment_part.strip()) if comment_part else {}
        )
        existing_data.update(new_data)
        final_comment = format_dict_to_data(existing_data)
        lines[idx] = code_part.rstrip() + f"  # {final_comment}"
    else:
        is_updating = False
        if idx > 0 and lines[idx - 1].strip().startswith("#"):
            comment_line_index = idx - 1
            comment_part = lines[comment_line_index].strip().lstrip(
                "#").strip()
            existing_data = parse_comment_data(comment_part)
            existing_data.update(new_data)
            final_comment = format_dict_to_data(existing_data)
            indentation = re.match(r"^\s*", lines[comment_line_index]).group(0)
            lines[comment_line_index] = f"{indentation}# {final_comment}"
            is_updating = True
        if not is_updating:
            final_comment = format_dict_to_data(new_data)
            # indent captures leading whitespace
            indentation_match = re.match(r"^\s*", lines[idx])
            indentation = indentation_match.group(
                0) if indentation_match else ""
            lines.insert(idx, f"{indentation}# {final_comment}")
            added_lines = 1
    try:
        with open(filepath, "w") as f:
            f.write("\n".join(lines))
        return {"success": True, "added_lines": added_lines}
    except Exception:
        return {"success": False, "added_lines": 0}


def get_node_metadata(source: str):
    return {
        "calls": get_call_metadata(source),
        "functions": get_function_metadata(source),
        "classes": get_class_metadata(source),
    }
