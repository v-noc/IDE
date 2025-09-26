import ast
from typing import List, Optional, Union

from .models import (
    AnnAssignSchema, ArgSchema, AssignSchema, AttributeSchema, BaseSchema, CallSchema,
    ClassSchema, FunctionSchema, ImportAliasSchema, ImportFromSchema, ImportSchema,
    KeywordSchema, NameSchema, SubscriptSchema
)
from .utils import (
    extract_annotation, extract_name_or_attribute, extract_position,
    extract_value
)


class SchemaConverter:
    """
    A stateless converter that translates ast.AST Schemas into Pydantic models.
    """

    def _convert_expression(
        self, node: ast.AST
    ) -> Optional[Union[BaseSchema, list, object]]:
        """
        Recursively converts an expression AST node into a Pydantic model.
        This is the core of handling nested structures like `a.b().k()`.
        """
        if isinstance(node, ast.Name):
            return NameSchema(name=node.id, position=extract_position(node))
        if isinstance(node, ast.Attribute):
            # Recursively convert the owner of the attribute (e.g., `a.b()` in `a.b().k`)
            value = self._convert_expression(node.value)
            return AttributeSchema(
                name=node.attr, value=value, position=extract_position(node)
            )
        if isinstance(node, ast.Call):
            # If we encounter a call, convert it fully.

            return self.convert_call(node)
        if isinstance(node, (ast.List, ast.Tuple)):
            # Handle list/tuple literals: [a(), b]
            return [self._convert_expression(elt) for elt in node.elts]
        if isinstance(node, ast.Constant):
            return node.value

        # Return None for unhandled expression types
        return None

    def convert_functiondef(
            self, Schema: ast.FunctionDef, returns: List[ast.Return]
    ) -> FunctionSchema:
        args: List[ArgSchema] = []
        if Schema.args:
            for arg in Schema.args.args:
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

        return_annotation = (
            extract_annotation(Schema.returns) if Schema.returns else None
        )

        return_values = []
        for return_Schema in returns:
            if return_Schema.value:
                value = extract_value(return_Schema.value)
                if value:
                    return_values.extend(value)

        return FunctionSchema(
            name=Schema.name or "anonymous",
            position=extract_position(Schema),
            args=args,
            return_annotation=return_annotation,
            return_values=return_values,
        )

    def convert_classdef(self, Schema: ast.ClassDef) -> ClassSchema:
        implements = []
        if Schema.bases:
            for base in Schema.bases:
                extracted = extract_name_or_attribute(base)
                if extracted:
                    implements.append(extracted)
        return ClassSchema(
            name=Schema.name, implements=implements, position=extract_position(
                Schema)
        )

    def convert_import(self, Schema: ast.Import) -> ImportSchema:
        names: list[ImportAliasSchema] = []
        for alias in Schema.names:
            names.append(
                ImportAliasSchema(
                    name=alias.name,
                    asname=alias.asname or alias.name,
                    position=extract_position(alias),
                )
            )
        return ImportSchema(names=names, position=extract_position(Schema))

    def convert_importfrom(self, Schema: ast.ImportFrom) -> ImportFromSchema:
        names: list[ImportAliasSchema] = []
        for alias in Schema.names:
            names.append(
                ImportAliasSchema(
                    name=alias.name,
                    asname=alias.asname or alias.name,
                    position=extract_position(alias),
                )
            )
        return ImportFromSchema(
            module_name=Schema.module,
            names=names,
            level=Schema.level,
            position=extract_position(Schema),
        )

    def convert_assign(self, Schema: ast.Assign) -> AssignSchema:
        targets: List[Union[NameSchema, AttributeSchema]] = []
        for target in Schema.targets:
            targets.extend(extract_value(target))

        value = []
        # We handle Call conversion in its own visitor method,
        # so we only extract non-call values here.
        if not isinstance(Schema.value, ast.Call):
            value = extract_value(Schema.value)

        return AssignSchema(
            targets=targets, value=value, position=extract_position(Schema)
        )

    def convert_annassign(self, Schema: ast.AnnAssign) -> AnnAssignSchema:
        target = extract_value(Schema.target)[0]
        annotation = extract_annotation(Schema.annotation)

        value = []
        if Schema.value and not isinstance(Schema.value, ast.Call):
            value = extract_value(Schema.value)

        return AnnAssignSchema(
            target=target,
            value=value,
            annotation=annotation,
            position=extract_position(Schema),
        )

    def _deconstruct_list_or_tuple(self, Schema: ast.AST):
        items = []
        if hasattr(Schema, "elts"):
            for elt in Schema.elts:
                items.extend(self._deconstruct_list_or_tuple(elt))
        elif isinstance(Schema, ast.Call):
            items.append(self.convert_call(Schema))
        else:
            value = extract_value(Schema)
            if value:
                items.extend(value)
        return items

    def convert_call(self, node: ast.Call) -> CallSchema:
        # Use the powerful _convert_expression to handle the function part
        func = self._convert_expression(node.func)

        # Convert args and keywords using the same recursive logic
        args = [self._convert_expression(arg) for arg in node.args]
        keywords = []
        for keyword in node.keywords:
            keywords.append(
                KeywordSchema(
                    name=keyword.arg,
                    value=self._convert_expression(keyword.value),
                    position=extract_position(keyword),
                )
            )

        return CallSchema(
            func=func, args=args, keywords=keywords, position=extract_position(
                node)
        )
