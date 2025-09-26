import ast
from .models import NodePosition, NameNode, AttributeNode, SubscriptNode
from typing import Optional, Union, List


def extract_position(node: ast.AST) -> NodePosition:
    return NodePosition(
        line_no=getattr(node, 'lineno', 0),
        col_offset=getattr(node, 'col_offset', 0),
        end_line_no=getattr(node, 'end_lineno', None),
        end_col_offset=getattr(node, 'end_col_offset', None)
    )


def extract_inner_types(node: ast.AST) -> List[Union[NameNode, AttributeNode]]:
    """
    Recursively traverses a complex annotation node and extracts a flat list
    of all NameNode and AttributeNode instances found within the slice of a
    Subscript node.
    """
    results: List[Union[NameNode, AttributeNode]] = []

    if isinstance(node, (ast.Name, ast.Attribute)):
        # Base case: If we find a name or attribute, extract it and add to
        # results.
        extracted_node = extract_name_or_attribute(node)
        if extracted_node:
            results.append(extracted_node)
    elif isinstance(node, ast.Subscript):
        # Only process the slice (inner types), not the value (e.g., 'Dict')
        results.extend(extract_inner_types(node.slice))
    elif isinstance(node, (ast.Tuple, ast.List)):
        # Recursive case: For (str, int), iterate and extract from each
        # element.
        for element in node.elts:
            results.extend(extract_inner_types(element))
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        # Recursive case: For str | int, extract from 'str' and from 'int'.
        results.extend(extract_inner_types(node.left))
        results.extend(extract_inner_types(node.right))

    return results


def extract_annotation(
    node: ast.AST
) -> Union[NameNode, AttributeNode, SubscriptNode, str]:
    """
    Extracts an annotation with a preference for structured nodes.
    - Returns NameNode/AttributeNode for simple types.
    - Returns SubscriptNode for complex generic types (e.g., List[...]).
    - Falls back to a string for forward references or other unsupported types.
    """
    # Path 1: Handle simple cases like `int` or `models.User` first.
    if isinstance(node, (ast.Name, ast.Attribute)):
        return extract_name_or_attribute(node)

    # Path 2: Handle complex subscripted types like `List[int]`.
    if isinstance(node, ast.Subscript):
        full_type_string = annotation_to_string(node)
        inner_types = extract_inner_types(node)

        return SubscriptNode(
            full_str=full_type_string,
            elements=inner_types,
            position=extract_position(node)
        )

    # Path 3: Fallback for everything else (forward refs, complex unions,
    # etc.).
    # The full string representation is the most reliable output.
    return annotation_to_string(node)


def extract_value(node: ast.AST) -> List[Union["NameNode", "AttributeNode"]]:
    """Recursively extract NameNode or AttributeNode(s) from an AST node.

    - Handles Tuple, List, Set (anything with `.elts`).
    - Recursively descends into nested structures.
    - Always returns a list (possibly empty).
    - Filters out None values.
    """
    results: List[Union["NameNode", "AttributeNode"]] = []

    if hasattr(node, "elts"):  # Tuple, List, Set, etc.
        for elt in node.elts:
            results.extend(extract_value(elt))  # recursive call
    else:
        if (extracted := extract_name_or_attribute(node)) is not None:
            results.append(extracted)

    return results


def extract_name_or_attribute(
    node: ast.AST
) -> Optional[Union[NameNode, AttributeNode]]:
    """Extract name or attribute nodes, handle nested calls like super()"""
    if isinstance(node, ast.Name):
        return NameNode(name=node.id, position=extract_position(node))
    elif isinstance(node, ast.Attribute):
        # Handle cases like super().method() where value might be a Call
        if isinstance(node.value, ast.Call):
            # For super().method(), we want to extract the Call as the value
            # Check if it's a super() call
            if (isinstance(node.value.func, ast.Name) and
                    node.value.func.id == 'super'):
                # Create a special NameNode for super() calls
                super_node = NameNode(
                    name='super',
                    position=extract_position(node.value.func)
                )
                return AttributeNode(
                    name=node.attr,
                    value=super_node,
                    position=extract_position(node)
                )
            else:
                # For other call().method() patterns, try to extract recursively
                call_value = extract_name_or_attribute(node.value.func)
                return AttributeNode(
                    name=node.attr,
                    value=call_value,
                    position=extract_position(node)
                )
        else:
            # Normal attribute access like obj.attr
            value = extract_name_or_attribute(node.value)
            return AttributeNode(
                name=node.attr,
                value=value,
                position=extract_position(node)
            )
    return None


def annotation_to_string(node: ast.AST) -> str:
    """Convert annotation to string - focused on type references"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Subscript):
        value = annotation_to_string(node.value)
        slice_str = annotation_to_string(node.slice)
        return f"{value}[{slice_str}]"
    elif isinstance(node, ast.Tuple):
        elements = [annotation_to_string(elt) for elt in node.elts]
        return ", ".join(elements)
    elif isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return f"'{node.value}'"
        return str(node.value)
    elif isinstance(node, ast.Attribute):
        value = annotation_to_string(node.value)
        return f"{value}.{node.attr}"
    elif isinstance(node, ast.List):
        elements = [annotation_to_string(elt) for elt in node.elts]
        return f"[{', '.join(elements)}]"
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left = annotation_to_string(node.left)
        right = annotation_to_string(node.right)
        return f"{left} | {right}"
    else:
        return f"<{type(node).__name__}>"
