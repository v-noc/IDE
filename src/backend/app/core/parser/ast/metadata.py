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


def _get_indentation(line: str) -> str:
    match = re.match(r"^\s*", line)
    return match.group(0) if match else ""


def _find_docstring_block(
    lines: List[str],
    def_line_index: int,
) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    """Locate the docstring block for a function/class.

    Returns a tuple of (docstring_start_idx, docstring_end_idx,
    docstring_text). If there is no docstring, returns (None, None, None).
    """
    # Determine body indentation by finding the first body line
    def_line = lines[def_line_index] if def_line_index < len(lines) else ""
    def_indent = _get_indentation(def_line)

    i = def_line_index + 1
    # Skip blank lines and comments between def and the first statement
    while i < len(lines) and (
        lines[i].strip() == "" or lines[i].lstrip().startswith("#")
    ):
        i += 1
    if i >= len(lines):
        return None, None, None

    body_line = lines[i]
    body_indent = _get_indentation(body_line)
    # If not more indented, there is no body
    if len(body_indent) <= len(def_indent):
        return None, None, None

    stripped = body_line.strip()
    triple = None
    if stripped.startswith('"""'):
        triple = '"""'
    elif stripped.startswith("'''"):
        triple = "'''"
    else:
        return None, None, None

    # Find the end of the triple-quoted string
    start_idx = i
    # If the opening and closing are on the same line
    if stripped.count(triple) >= 2 and stripped.endswith(triple):
        content = stripped[len(triple):-len(triple)].strip()
        return start_idx, start_idx, content

    # Otherwise, scan until we find the closing delimiter
    content_lines: List[str] = []
    # Remove opening delimiter on first line
    first_line_after = body_line.split(triple, 1)[1]
    if first_line_after:
        content_lines.append(first_line_after)
    j = i + 1
    while j < len(lines):
        line = lines[j]
        if triple in line:
            before, _after = line.split(triple, 1)
            content_lines.append(before)
            end_idx = j
            # Join and strip trailing newlines/spaces
            content_text = "\n".join(content_lines).strip()
            return start_idx, end_idx, content_text
        else:
            content_lines.append(line)
        j += 1

    # Unterminated docstring
    return None, None, None


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
