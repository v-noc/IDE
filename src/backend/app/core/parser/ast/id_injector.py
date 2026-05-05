import libcst as cst
from uuid import uuid4
import re
import textwrap
from typing import Optional, Tuple, Dict


# Stable scope id: exact tag "ID" followed by ":" (not GRID, GUID, etc.).
_ID_LINE_RE = re.compile(
    r"(?:^|[\r\n])\s*ID\s*:\s*\S+",
    re.MULTILINE,
)


class IDInjector(cst.CSTTransformer):
    def __init__(self):
        self.modified = False

    def _extract_metadata(self, docstring: str) -> Dict[str, str]:
        if not docstring:
            return {}
        result: Dict[str, str] = {}
        id_m = re.search(
            r"(?:^|[\r\n])\s*ID\s*:\s*(\S+)",
            docstring,
            re.MULTILINE,
        )
        if id_m:
            result["ID"] = id_m.group(1)
        pairs = re.findall(r"(\S+)\s*:\s*(\S+)", docstring)
        for k, v in pairs:
            if k == "ID":
                continue
            result[k] = v
        return result

    def _docstring_declares_id(self, docstring: Optional[str]) -> bool:
        """True only if docstring contains an ``ID: <value>`` tag line."""
        if not docstring:
            return False
        return _ID_LINE_RE.search(docstring) is not None

    def _build_docstring(self, original_doc: Optional[str], new_metadata: Dict[str, str]) -> str:
        content = (original_doc or "").rstrip()

        # Remove existing keys we are about to update
        for key in new_metadata.keys():
            if key == "ID":
                pattern = re.compile(
                    r"(?:^|[\r\n])\s*ID\s*:\s*\S+",
                    re.MULTILINE,
                )
            else:
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

    def _docstring_literal(self, text: str) -> cst.SimpleString:
        """Build a :class:`cst.SimpleString` node for *text* as a triple-quoted docstring."""
        if '"""' not in text:
            return cst.SimpleString(f'"""{text}"""')
        if "'''" not in text:
            return cst.SimpleString(f"'''{text}'''")
        escaped = text.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
        return cst.SimpleString(f'"""{escaped}"""')

    def _replace_first_doc_expr_in_line(
        self,
        line: cst.SimpleStatementLine,
        new_value: cst.BaseExpression,
    ) -> cst.SimpleStatementLine | None:
        if not line.body:
            return None
        first = line.body[0]
        if not isinstance(first, cst.Expr):
            return None
        if not isinstance(first.value, (cst.SimpleString, cst.ConcatenatedString)):
            return None
        new_first = cst.Expr(value=new_value, semicolon=first.semicolon)
        return line.with_changes(body=(new_first,) + tuple(line.body[1:]))

    def _inject_into_indented_block(
        self,
        block: cst.IndentedBlock,
        current_doc: str | None,
        new_lit: cst.SimpleString,
    ) -> cst.IndentedBlock | None:
        statements = list(block.body)
        if current_doc is not None:
            if not statements:
                return None
            first_line = statements[0]
            if not isinstance(first_line, cst.SimpleStatementLine):
                return None
            updated = self._replace_first_doc_expr_in_line(first_line, new_lit)
            if updated is None:
                return None
            statements[0] = updated
            return block.with_changes(body=tuple(statements))
        if not statements:
            return None
        new_stmt = cst.SimpleStatementLine(
            body=(cst.Expr(value=new_lit),),
            trailing_whitespace=cst.TrailingWhitespace(newline=cst.Newline()),
        )
        return block.with_changes(body=(new_stmt,) + tuple(statements))

    def _inject_into_simple_statement_suite(
        self,
        suite: cst.SimpleStatementSuite,
        current_doc: str | None,
        new_lit: cst.SimpleString,
    ) -> cst.SimpleStatementSuite | None:
        smts = list(suite.body)
        if current_doc is not None:
            if not smts:
                return None
            first = smts[0]
            if not isinstance(first, cst.Expr):
                return None
            if not isinstance(first.value, (cst.SimpleString, cst.ConcatenatedString)):
                return None
            smts[0] = cst.Expr(value=new_lit, semicolon=first.semicolon)
            return suite.with_changes(body=tuple(smts))
        if not smts:
            return None
        new_first = cst.Expr(
            value=new_lit,
            semicolon=cst.Semicolon(
                whitespace_before=cst.SimpleWhitespace(""),
                whitespace_after=cst.SimpleWhitespace(" "),
            ),
        )
        return suite.with_changes(body=(new_first,) + tuple(smts))

    def _add_id_to_docstring(self, body: cst.BaseSuite, current_doc: str | None) -> cst.BaseSuite:
        # Require explicit ``ID: <value>`` (not bare "ID" or GRID:, etc.)
        if current_doc and self._docstring_declares_id(current_doc):
            return body

        id_value = str(uuid4())
        new_doc_content = self._build_docstring(current_doc, {"ID": id_value})
        new_lit = self._docstring_literal(new_doc_content)

        if isinstance(body, cst.SimpleStatementSuite):
            new_body = self._inject_into_simple_statement_suite(body, current_doc, new_lit)
        elif isinstance(body, cst.IndentedBlock):
            new_body = self._inject_into_indented_block(body, current_doc, new_lit)
        else:
            new_body = None

        if new_body is None:
            return body

        self.modified = True
        return new_body

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
        print(f"Exception: {e}")
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
