import re
from typing import Dict, List

from .ast_comment import parse, walk, Comment


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


def build_comment_map(tree) -> Dict[int, str]:
    comment_map: Dict[int, str] = {}
    for node in walk(tree):
        if isinstance(node, Comment):
            comment_map[node.lineno] = clean_comment_text(node.value)
    return comment_map


def resolve_metadata_for_line(
    comment_map: Dict[int, str], lines: List[str], line_no: int
) -> Dict[str, str]:
    # Prefer inline
    if line_no in comment_map:
        parsed = parse_comment_data(comment_map[line_no])
        if parsed:
            return parsed

    # Walk upward skipping blank lines
    idx = line_no - 1
    while idx > 0:
        if idx in comment_map:
            parsed = parse_comment_data(comment_map[idx])
            if parsed:
                return parsed
            break
        if idx - 1 < len(lines) and lines[idx - 1].strip() == "":
            idx -= 1
            continue
        break
    return {}


def add_comment(
    filepath: str,
    comment_text: str,
    line_number: int,
    position: str = "inline",
) -> Dict[str, int | bool]:
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
