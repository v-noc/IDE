import re
from typing import Dict, List

from .ast_comment import (
    parse,
    walk,
    Comment,
    Expr,
    Call,
    Name,
    FunctionDef,
    ClassDef,
)

# A simple regex to parse "Key: Value" pairs
METADATA_REGEX = re.compile(r"(\w+):\s*([^,]+)")


def _clean_comment_text(text: str) -> str:
    return text.lstrip("#").strip()


def _parse_comment_data(text: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    cleaned = _clean_comment_text(text)
    for match in METADATA_REGEX.finditer(cleaned):
        key = match.group(1).strip()
        value = match.group(2).strip()
        data[key] = value
    return data


def _format_dict_to_data(data: Dict[str, str]) -> str:
    return ", ".join([f"{k}: {v}" for k, v in data.items()])


def build_comment_map(tree) -> Dict[int, str]:
    comment_map: Dict[int, str] = {}
    for node in walk(tree):
        if isinstance(node, Comment):
            comment_map[node.lineno] = _clean_comment_text(node.value)
    return comment_map


def _extract_metadata_for_line(
    comment_map: Dict[int, str], line_no: int
) -> Dict[str, str]:
    if line_no in comment_map:
        parsed = _parse_comment_data(comment_map[line_no])
        if parsed:
            return parsed
    if (line_no - 1) in comment_map:
        parsed = _parse_comment_data(comment_map[line_no - 1])
        if parsed:
            return parsed
    return {}


def get_call_metadata(source: str) -> List[Dict[str, object]]:
    try:
        tree = parse(source)
    except Exception:
        return []
    comment_map = build_comment_map(tree)
    results: List[Dict[str, object]] = []
    for node in walk(tree):
        if isinstance(node, Expr) and isinstance(node.value, Call):
            call_node: Call = node.value
            metadata = _extract_metadata_for_line(
                comment_map,
                call_node.lineno,
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
    results: List[Dict[str, object]] = []
    for node in walk(tree):
        if isinstance(node, FunctionDef):
            metadata = _extract_metadata_for_line(comment_map, node.lineno)
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
    results: List[Dict[str, object]] = []
    for node in walk(tree):
        if isinstance(node, ClassDef):
            metadata = _extract_metadata_for_line(comment_map, node.lineno)
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
) -> bool:
    if position not in ["inline", "above"]:
        return False
    try:
        with open(filepath, "r") as f:
            source = f.read()
    except Exception:
        return False
    try:
        parse(source)
    except Exception:
        return False
    lines = source.splitlines()
    idx = max(0, line_number - 1)
    new_data = _parse_comment_data(comment_text)
    if position == "inline":
        original_line = lines[idx] if idx < len(lines) else ""
        if "#" in original_line:
            code_part, comment_part = original_line.split("#", 1)
        else:
            code_part, comment_part = original_line, ""
        existing_data = (
            _parse_comment_data(comment_part.strip()) if comment_part else {}
        )
        existing_data.update(new_data)
        final_comment = _format_dict_to_data(existing_data)
        lines[idx] = code_part.rstrip() + f"  # {final_comment}"
    else:
        is_updating = False
        if idx > 0 and lines[idx - 1].strip().startswith("#"):
            comment_line_index = idx - 1
            comment_part = lines[comment_line_index].strip().lstrip(
                "#").strip()
            existing_data = _parse_comment_data(comment_part)
            existing_data.update(new_data)
            final_comment = _format_dict_to_data(existing_data)
            indentation = re.match(r"^\s*", lines[comment_line_index]).group(0)
            lines[comment_line_index] = f"{indentation}# {final_comment}"
            is_updating = True
        if not is_updating:
            final_comment = _format_dict_to_data(new_data)
            # indent captures leading whitespace
            indentation_match = re.match(r"^\s*", lines[idx])
            indentation = indentation_match.group(
                0) if indentation_match else ""
            lines.insert(idx, f"{indentation}# {final_comment}")
    try:
        with open(filepath, "w") as f:
            f.write("\n".join(lines))
        return True
    except Exception:
        return False


def get_node_metadata(source: str):
    return {
        "calls": get_call_metadata(source),
        "functions": get_function_metadata(source),
        "classes": get_class_metadata(source),
    }
