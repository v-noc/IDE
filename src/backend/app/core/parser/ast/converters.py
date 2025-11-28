def _extract_id_from_docstring(node) -> Optional[str]:
    """Extract ID from a one-line docstring containing "ID: <value>"."""
    try:
        # Works for FunctionDef and ClassDef
        if not hasattr(node, "body") or not node.body:
            return None
        first_stmt = node.body[0]
        # Docstring is a string constant as the first statement
        if isinstance(first_stmt, Expr) and isinstance(first_stmt.value, Constant):
            value = (
                first_stmt.value.value if hasattr(
                    first_stmt.value, "value") else None
            )
            if isinstance(value, str):
                doc = value.strip()
                match = re.search(r"\bID:\s*([^\s]+)", doc)
                if match:
                    return match.group(1).strip()
    except Exception:
        return None
    return None


class CodeNodeConverter:
