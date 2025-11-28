import libcst as cst
import libcst.metadata as m
from typing import List, Dict, Tuple, Optional
from uuid import uuid4
import re


def build_docstring(
    original_doc: Optional[str], new_metadata: Dict[str, str]
) -> str:
    """
    Build a plain docstring text by appending/updating simple
    "key: value" entries.
    - Removes any legacy '--- metadata: ... ---' blocks.
    - Removes existing occurrences for keys present in new_metadata.
    - Appends new "key: value" lines (values are single tokens).
    """
    content = (original_doc or "").rstrip()

    # Strip legacy metadata block if present
    if content:
        content = re.sub(
            r"\s*---\s*metadata:\s*.*?\s*---\s*$",
            "",
            content,
            flags=re.DOTALL | re.IGNORECASE,
        ).rstrip()

    if not new_metadata:
        return content

    # Remove existing occurrences of keys to be updated
    for key in new_metadata.keys():
        # Remove occurrences like "key : value" with single-token value
        pattern = re.compile(
            rf"(^|(?<=\s)){re.escape(key)}\s*:\s*\S+(?=\s|$)",
            re.MULTILINE,
        )
        content = pattern.sub("", content).strip()

        # Also clear any standalone line fully dedicated to the pair
        line_pattern = re.compile(
            rf"^\s*{re.escape(key)}\s*:\s*\S+\s*$", re.MULTILINE
        )
        content = line_pattern.sub("", content).strip()

    # Build new key:value lines
    kv_lines = [f"{k}: {v}" for k, v in new_metadata.items()]
    kv_text = "\n".join(kv_lines)

    return f"{content}\n\n{kv_text}".strip() if content else kv_text


def extract_metadata(docstring: Optional[str]) -> Dict[str, str]:
    """
    Extract all occurrences of key:value pairs from a docstring.
    - Allows optional spaces around ':'
    - Values are single tokens up to the next whitespace
    - Later occurrences overwrite earlier ones
    """
    if not docstring:
        return {}

    pairs = re.findall(r"(\S+)\s*:\s*(\S+)", docstring)
    result: Dict[str, str] = {}
    for key, value in pairs:
        result[key] = value
    return result


class DocstringPreProcessor(cst.CSTTransformer):

    def _add_id_to_docstring(self, body: cst.IndentedBlock, current_doc: str | None) -> cst.IndentedBlock:
        id_value = str(uuid4())

        if current_doc is not None:
            extracted_metadata = extract_metadata(current_doc)
            if extracted_metadata.get("ID") is not None:
                id = extracted_metadata.get("ID")

                return body
            else:
                new_doc_content = build_docstring(
                    current_doc, {"ID": id_value})
        else:
            new_doc_content = build_docstring(None, {"ID": id_value})

        statements = body.body
        # Replace existing (assume first stmt is docstring Expr)
        if current_doc is not None:
            if (
                statements
                and isinstance(statements[0], cst.SimpleStatementLine)
                and len(statements[0].body) == 1
                and isinstance(statements[0].body[0], cst.Expr)
                and isinstance(statements[0].body[0].value, cst.SimpleString)
            ):
                old_expr = statements[0].body[0]
                new_expr = old_expr.with_changes(
                    value=cst.SimpleString(f'"""{new_doc_content}"""')
                )
                new_stmt = statements[0].with_changes(body=(new_expr,))
                new_body_statements = (new_stmt,) + statements[1:]
            else:
                return body  # Skip if not standard docstring

        else:
            # Insert new at start
            new_stmt = cst.SimpleStatementLine(
                body=(
                    cst.Expr(
                        value=cst.SimpleString(
                            f'"""{new_doc_content}"""'
                        )
                    ),
                ),
                trailing_whitespace=cst.TrailingWhitespace(
                    newline=cst.Newline()),
            )
            new_body_statements = (new_stmt,) + statements

        return body.with_changes(body=new_body_statements)

    def leave_ClassDef(
        self, original_node: cst.ClassDef, updated_node: cst.ClassDef
    ) -> cst.ClassDef:
        try:
            current_doc = original_node.get_docstring(clean=True)
            new_body = self._add_id_to_docstring(
                updated_node.body, current_doc)

            return updated_node.with_changes(body=new_body)
        except Exception as e:
            print(f"Error adding ID to docstring: {e}")
            return updated_node

    def leave_FunctionDef(
        self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef
    ) -> cst.FunctionDef:
        try:
            current_doc = original_node.get_docstring(clean=True)
            new_body = self._add_id_to_docstring(
                updated_node.body, current_doc)
            return updated_node.with_changes(body=new_body)
        except Exception as e:
            print(f"Error adding ID to docstring: {e}")
            return updated_node
