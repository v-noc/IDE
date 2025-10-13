import re
from typing import Dict, List, Optional, Tuple

from ast import parse, walk, FunctionDef, ClassDef, get_docstring
import ast


# Centralized regex and helpers for metadata parsing and formatting
METADATA_REGEX = re.compile(r"(\w+):\s*([^,]+)")


def clean_comment_text(text: str) -> str:
    return text.lstrip("#").strip()


def parse_comment_data(text: str) -> Dict[str, str]:
    data: Dict[str, str] = {}
    cleaned = clean_comment_text(text)
    for match in METADATA_REGEX.finditer(cleaned):
        key = match.group(1).strip()
        value = match.group(2).strip()
        data[key] = value
    return data


def format_dict_to_data(data: Dict[str, str]) -> str:
    return ", ".join([f"{k}: {v}" for k, v in data.items()])


def _parse_docstring_metadata_from_node(node) -> Dict[str, str]:
    """Parse metadata dict from a node's docstring."""
    try:
        doc = get_docstring(node)
        if not doc:
            return {}
        return parse_comment_data(doc)
    except Exception:
        return {}


def build_comment_map(tree) -> Dict[int, str]:
    """Build a map of def/class line numbers to docstring metadata text."""
    comment_map: Dict[int, str] = {}
    for node in walk(tree):
        if isinstance(node, (FunctionDef, ClassDef)):
            data = _parse_docstring_metadata_from_node(node)
            if data:
                comment_map[node.lineno] = format_dict_to_data(data)
    return comment_map


def resolve_metadata_for_line(
    comment_map: Dict[int, str], lines: List[str], line_no: int
) -> Dict[str, str]:
    """Return parsed metadata if present exactly at the def/class line."""
    if line_no in comment_map:
        parsed = parse_comment_data(comment_map[line_no])
        if parsed:
            return parsed
    return {}


def add_comment(
    filepath: str,
    comment_text: str,
    line_number: int,

) -> Dict[str, int | bool]:
    """Write a one-line docstring via AST unparse at def/class lineno.

    Keeps it to a single line like: ID: <value>
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

    target = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and \
                getattr(n, "lineno", None) == line_number:
            target = n
            break

    if target is None:
        return {"success": False, "added_lines": 0}

    data = parse_comment_data(comment_text)
    final_comment = format_dict_to_data(data) if data else comment_text.strip()
    # Single-line docstring string value; quotes added by unparse
    doc_value = f" {final_comment} "

    had_doc = False
    if target.body and isinstance(target.body[0], ast.Expr) and \
            isinstance(target.body[0].value, ast.Constant) and \
            isinstance(target.body[0].value.value, str):
        target.body[0].value = ast.Constant(value=doc_value)
        had_doc = True
    else:
        doc_expr = ast.Expr(value=ast.Constant(value=doc_value))
        target.body.insert(0, doc_expr)

    try:
        ast.fix_missing_locations(tree)
        new_source = ast.unparse(tree)
    except Exception:
        return {"success": False, "added_lines": 0}

    try:
        with open(filepath, "w") as f:
            f.write(new_source)
        return {"success": True, "added_lines": 0 if had_doc else 1}
    except Exception:
        return {"success": False, "added_lines": 0}
