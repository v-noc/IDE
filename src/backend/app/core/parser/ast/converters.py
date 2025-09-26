import ast
from typing import List, Union

from .models import (
    AnnAssignNode, ArgNode, AssignNode, AttributeNode, BaseNode, CallNode,
    ClassNode, FunctionNode, ImportAliasNode, ImportFromNode, ImportNode,
    KeywordNode, NameNode, SubscriptNode
)
from .utils import (
    extract_annotation, extract_name_or_attribute, extract_position,
    extract_value
)


class NodeConverter:
    """
A stateless converter that translates ast.AST nodes into Pydantic models.
"""

    def convert_functiondef(
            self, node: ast.FunctionDef, returns: List[ast.Return]
    ) -> FunctionNode:
        args: List[ArgNode] = []
        if node.args:
            for arg in node.args.args:
                annotation = (
                    extract_annotation(
                        arg.annotation) if arg.annotation else None
                )
                args.append(
                    ArgNode(
                        name=arg.arg,
                        annotation=annotation,
                        position=extract_position(arg),
                    )
                )

        return_annotation = (
            extract_annotation(node.returns) if node.returns else None
        )

        return_values = []
        for return_node in returns:
            if return_node.value:
                value = extract_value(return_node.value)
                if value:
                    return_values.extend(value)

        return FunctionNode(
            name=node.name or "anonymous",
            position=extract_position(node),
            args=args,
            return_annotation=return_annotation,
            return_values=return_values,
        )

    def convert_classdef(self, node: ast.ClassDef) -> ClassNode:
        implements = []
        if node.bases:
            for base in node.bases:
                extracted = extract_name_or_attribute(base)
                if extracted:
                    implements.append(extracted)
        return ClassNode(
            name=node.name, implements=implements, position=extract_position(
                node)
        )

    def convert_import(self, node: ast.Import) -> ImportNode:
        names: list[ImportAliasNode] = []
        for alias in node.names:
            names.append(
                ImportAliasNode(
                    name=alias.name,
                    asname=alias.asname or alias.name,
                    position=extract_position(alias),
                )
            )
        return ImportNode(names=names, position=extract_position(node))

    def convert_importfrom(self, node: ast.ImportFrom) -> ImportFromNode:
        names: list[ImportAliasNode] = []
        for alias in node.names:
            names.append(
                ImportAliasNode(
                    name=alias.name,
                    asname=alias.asname or alias.name,
                    position=extract_position(alias),
                )
            )
        return ImportFromNode(
            module_name=node.module,
            names=names,
            level=node.level,
            position=extract_position(node),
        )

    def convert_assign(self, node: ast.Assign) -> AssignNode:
        targets: List[Union[NameNode, AttributeNode]] = []
        for target in node.targets:
            targets.extend(extract_value(target))

        value = []
        # We handle Call conversion in its own visitor method,
        # so we only extract non-call values here.
        if not isinstance(node.value, ast.Call):
            value = extract_value(node.value)

        return AssignNode(
            targets=targets, value=value, position=extract_position(node)
        )

    def convert_annassign(self, node: ast.AnnAssign) -> AnnAssignNode:
        target = extract_value(node.target)[0]
        annotation = extract_annotation(node.annotation)

        value = []
        if node.value and not isinstance(node.value, ast.Call):
            value = extract_value(node.value)

        return AnnAssignNode(
            target=target,
            value=value,
            annotation=annotation,
            position=extract_position(node),
        )

    def _deconstruct_list_or_tuple(self, node: ast.AST):
        items = []
        if hasattr(node, "elts"):
            for elt in node.elts:
                items.extend(self._deconstruct_list_or_tuple(elt))
        elif isinstance(node, ast.Call):
            items.append(self.convert_call(node))
        else:
            value = extract_value(node)
            if value:
                items.extend(value)
        return items

    def convert_call(self, node: ast.Call) -> CallNode:
        func: Union[NameNode, AttributeNode, CallNode, None] = None
        if isinstance(node.func, (ast.Name, ast.Attribute)):
            func = extract_value(node.func)[0]
        elif isinstance(node.func, ast.Call):
            func = self.convert_call(node.func)

        args = []
        for arg in node.args:
            if isinstance(arg, (ast.Name, ast.Attribute)):
                args.extend(extract_value(arg))
            elif hasattr(arg, "elts"):
                args.append(self._deconstruct_list_or_tuple(arg))
            elif isinstance(arg, ast.Call):
                args.append(self.convert_call(arg))
            else:
                # Placeholder for constants, etc.
                args.append(None)

        keywords = []
        for keyword in node.keywords:
            value: Union[NameNode, AttributeNode, CallNode, None] = None
            if isinstance(keyword.value, (ast.Name, ast.Attribute)):
                value = extract_value(keyword.value)[0]
            elif isinstance(keyword.value, ast.Call):
                value = self.convert_call(keyword.value)
            keywords.append(
                KeywordNode(
                    name=keyword.arg, value=value, position=extract_position(
                        keyword)
                )
            )

        return CallNode(
            func=func, args=args, keywords=keywords, position=extract_position(
                node)
        )
