from ast import (
    AST,
    Name,
    Attribute,
    Call,
    Expr,
    Constant,
    FunctionDef,
    Return,
    ClassDef,
    Import,
    ImportFrom,
    Assign,
    AnnAssign,
)
from typing import List, Optional, Union
import re
from .models import (
    AnnAssignSchema,
    ArgSchema,
    AssignSchema,
    AttributeSchema,
    BaseSchema,
    CallSchema,
    ClassSchema,
    FunctionSchema,
    ImportAliasSchema,
    ImportFromSchema,
    ImportSchema,
    KeywordSchema,
    NameSchema,
)
from .utils import (
    extract_annotation,
    extract_name_or_attribute,
    extract_position,
    extract_value,
)

# no metadata imports needed for simple docstring ID extraction


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


class SchemaConverter:
    """
    A stateless converter that translates ast.AST Schemas into Pydantic models.
    """

    def _convert_expression(
        self, node: AST
    ) -> Optional[Union[BaseSchema, list, object]]:
        """
        Recursively converts an expression AST node into a Pydantic model.
        This is the core of handling nested structures like `a.b().k()`.
        """
        if isinstance(node, Name):
            return NameSchema(name=node.id, position=extract_position(node))
        if isinstance(node, Attribute):
            # Recursively convert the owner of the attribute
            # (e.g., `a.b()` in `a.b().k`)
            value = self._convert_expression(node.value)
            return AttributeSchema(
                name=node.attr,
                value=value,
                position=extract_position(node),
            )
        if isinstance(node, Call):
            # If we encounter a call, convert it fully.
            if isinstance(node.func, Name) and node.func.id == "super":
                super_node = NameSchema(
                    name="super",
                    position=extract_position(node),
                )
                return super_node

            return self.convert_call(node)

        # Todo: Handle list/tuple literals: [a(), b]

        # if isinstance(node, (AstList, AstTuple)):
        #     # Handle list/tuple literals: [a(), b]
        #     return [self._convert_expression(elt) for elt in node.elts]
        # if isinstance(node, Constant):
        #     return None

        # Return None for unhandled expression types
        return None

    def convert_functiondef(
        self, node: FunctionDef, returns: List[Return]
    ) -> FunctionSchema:
        args: List[ArgSchema] = []
        func_id = _extract_id_from_docstring(node)

        if node.args:
            for arg in node.args.args:
                annotation = (
                    extract_annotation(
                        arg.annotation) if arg.annotation else None
                )
                args.append(
                    ArgSchema(
                        name=arg.arg,
                        annotation=annotation,
                        position=extract_position(arg),
                    )
                )

        return_annotation = extract_annotation(
            node.returns) if node.returns else None

        return_values = []
        for return_Schema in returns:
            if return_Schema.value:
                value = extract_value(return_Schema.value)
                if value:
                    return_values.extend(value)

        return FunctionSchema(
            id=func_id,
            name=node.name or "anonymous",
            position=extract_position(node),
            args=args,
            return_annotation=return_annotation,
            return_values=return_values,
        )

    def convert_classdef(self, node: ClassDef) -> ClassSchema:
        implements = []
        class_id = _extract_id_from_docstring(node)

        if node.bases:
            for base in node.bases:
                extracted = extract_name_or_attribute(base)
                if extracted:
                    implements.append(extracted)
        return ClassSchema(
            id=class_id,
            name=node.name,
            implements=implements,
            position=extract_position(node),
        )

    def convert_import(self, node: Import) -> ImportSchema:
        names: list[ImportAliasSchema] = []
        for alias in node.names:
            names.append(
                ImportAliasSchema(
                    name=alias.name,
                    asname=alias.asname or alias.name,
                    position=extract_position(alias),
                )
            )
        return ImportSchema(names=names, position=extract_position(node))

    def convert_importfrom(self, node: ImportFrom) -> ImportFromSchema:
        names: list[ImportAliasSchema] = []
        for alias in node.names:
            names.append(
                ImportAliasSchema(
                    name=alias.name,
                    asname=alias.asname or alias.name,
                    position=extract_position(alias),
                )
            )
        return ImportFromSchema(
            module_name=node.module,
            names=names,
            level=node.level,
            position=extract_position(node),
        )

    def convert_assign(self, node: Assign) -> AssignSchema:
        targets = [
            extract_name_or_attribute(t)
            for t in node.targets
            if extract_name_or_attribute(t)
        ]
        value = self._convert_expression(node.value)

        # The value can be a single item or a list from a tuple/list expression
        value_list = value if isinstance(value, list) else [value]

        return AssignSchema(
            targets=targets, value=value_list, position=extract_position(node)
        )

    def convert_annassign(self, node: AnnAssign) -> AnnAssignSchema:
        target = extract_value(node.target)[0]
        annotation = extract_annotation(node.annotation)

        value = []
        if node.value and not isinstance(node.value, Call):
            value = extract_value(node.value)

        return AnnAssignSchema(
            target=target,
            value=value,
            annotation=annotation,
            position=extract_position(node),
        )

    def _deconstruct_list_or_tuple(self, node: AST):
        items = []
        if hasattr(node, "elts"):
            for elt in node.elts:
                items.extend(self._deconstruct_list_or_tuple(elt))
        elif isinstance(node, Call):
            items.append(self.convert_call(node))
        else:
            value = extract_value(node)
            if value:
                items.extend(value)
        return items

    def convert_call(self, node: Call) -> CallSchema:
        try:
            # Use the powerful _convert_expression to handle the function part
            func = self._convert_expression(node.func)

            # Convert args and keywords using the same recursive logic
            args = [self._convert_expression(arg) for arg in node.args]
            keywords = []
            for keyword in node.keywords:
                kw_name = keyword.arg if isinstance(keyword.arg, str) else None
                keywords.append(
                    KeywordSchema(
                        name=kw_name,
                        value=self._convert_expression(keyword.value),
                        position=extract_position(keyword),
                    )
                )

            call_id = None

            return CallSchema(
                id=call_id,
                func=func,
                args=args,
                keywords=keywords,
                position=extract_position(node),
            )

        except Exception as e:
            print(f"Error converting call node: {e}")
            return None
