import libcst as cst
from uuid import uuid4
import re
import textwrap
from typing import Optional, Tuple, Dict


class IDInjector(cst.CSTTransformer):
    def __init__(self):
        self.modified = False

    def _extract_metadata(self, docstring: str) -> Dict[str, str]:
        if not docstring:
            return {}
        pairs = re.findall(r"(\S+)\s*:\s*(\S+)", docstring)
        return {k: v for k, v in pairs}

    def _build_docstring(self, original_doc: Optional[str], new_metadata: Dict[str, str]) -> str:
        content = (original_doc or "").rstrip()

        # Remove existing keys we are about to update
        for key in new_metadata.keys():
            pattern = re.compile(
                rf"(^|(?<=\s)){re.escape(key)}\s*:\s*\S+(?=\s|$)",
                re.MULTILINE,
            )
            content = pattern.sub("", content)

        # Format metadata lines cleanly
        kv_lines = [f"{k}: {v}" for k, v in new_metadata.items()]
        kv_text = "\n".join(kv_lines)

        # Combine content and metadata with proper formatting
        if content:
            # Dedent and normalize the original content
            dedented_content = textwrap.dedent(content)
            # Combine with metadata, ensuring proper spacing
            result = f"{dedented_content}\n\n{kv_text}"
        else:
            result = kv_text

        # Final dedent to ensure consistent indentation
        return textwrap.dedent(result)

    def _add_id_to_docstring(self, body: cst.IndentedBlock, current_doc: str | None) -> cst.IndentedBlock:
        # Check if ID exists
        if current_doc:
            metadata = self._extract_metadata(current_doc)
            if "ID" in metadata:
                return body  # ID exists, do nothing

        # ID missing, we need to modify
        self.modified = True
        id_value = str(uuid4())
        new_doc_content = self._build_docstring(current_doc, {"ID": id_value})

        statements = body.body

        # Replace existing docstring
        if current_doc is not None:
            if (
               statements
               and isinstance(statements[0], cst.SimpleStatementLine)
               and len(statements[0].body) == 1
               and isinstance(statements[0].body[0], cst.Expr)
               and isinstance(statements[0].body[0].value, cst.SimpleString)
               ):
                old_expr = statements[0].body[0]
                # Use triple quotes for docstrings
                new_expr = old_expr.with_changes(
                    value=cst.SimpleString(f'"""{new_doc_content}"""')
                )
                new_stmt = statements[0].with_changes(body=(new_expr,))
                new_body_statements = (new_stmt,) + statements[1:]
            else:
                # Fallback if structure is weird, but we detected a docstring earlier?
                # If get_docstring found it, it should be here.
                return body
        else:
            # Insert new docstring at start
            new_stmt = cst.SimpleStatementLine(
                body=(
                    cst.Expr(
                        value=cst.SimpleString(f'"""{new_doc_content}"""')
                    ),
                ),
                trailing_whitespace=cst.TrailingWhitespace(
                    newline=cst.Newline()
                ),
            )
            new_body_statements = (new_stmt,) + statements

        return body.with_changes(body=new_body_statements)

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        current_doc = original_node.get_docstring(clean=True)
        return updated_node.with_changes(body=self._add_id_to_docstring(updated_node.body, current_doc))

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        current_doc = original_node.get_docstring(clean=True)
        return updated_node.with_changes(body=self._add_id_to_docstring(updated_node.body, current_doc))


def inject_ids(content: str) -> Tuple[str, bool]:
    """
    Parses content, injects IDs where missing, and returns (new_content, was_modified).
    """
    try:
        module = cst.parse_module(content)
        transformer = IDInjector()
        new_module = module.visit(transformer)
        if transformer.modified:
            return new_module.code, True
        return content, False
    except Exception as e:
        return content, False


def inject_module_metadata(content: str, metadata: Dict[str, str]) -> Tuple[str, bool]:
    """
    Injects key-value metadata into the module-level docstring.
    Preserves existing metadata unless overwritten.
    """
    try:
        module = cst.parse_module(content)
        current_doc = module.get_docstring(clean=True)

        injector = IDInjector()
        # Check if we actually need to change anything
        current_metadata = injector._extract_metadata(current_doc)
        needs_update = False
        for k, v in metadata.items():
            if current_metadata.get(k) != v:
                needs_update = True
                break

        if not needs_update:
            return content, False

        # Reuse the docstring building logic from IDInjector
        # We temporarily merge current and new metadata for the build
        combined_metadata = current_metadata.copy()
        combined_metadata.update(metadata)

        # _build_docstring logic handles merging/replacing
        new_doc_content = injector._build_docstring(current_doc, metadata)

        # Create new body with updated docstring
        statements = module.body
        new_body_statements = statements

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
            # Insert new docstring at start
            new_stmt = cst.SimpleStatementLine(
                body=(
                    cst.Expr(
                        value=cst.SimpleString(f'"""{new_doc_content}"""')
                    ),
                ),
                trailing_whitespace=cst.TrailingWhitespace(
                    newline=cst.Newline()
                ),
            )
            new_body_statements = (new_stmt,) + statements

        new_module = module.with_changes(body=new_body_statements)
        return new_module.code, True

    except Exception as e:
        # Fallback or log error? For now return original
        return content, False
