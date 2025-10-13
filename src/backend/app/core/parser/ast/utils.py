import ast
from .models import SchemaPosition, NameSchema, AttributeSchema, SubscriptSchema
from typing import Optional, Union, List


def extract_position(Schema: ast.AST) -> SchemaPosition:
    return SchemaPosition(
        line_no=getattr(Schema, 'lineno', 0),
        col_offset=getattr(Schema, 'col_offset', 0),
        end_line_no=getattr(Schema, 'end_lineno', None),
        end_col_offset=getattr(Schema, 'end_col_offset', None)
    )


def extract_inner_types(Schema: ast.AST) -> List[Union[NameSchema, AttributeSchema]]:
    """
    Recursively traverses a complex annotation Schema and extracts a flat list
    of all NameSchema and AttributeSchema instances found within the slice of a
    Subscript Schema.
    """
    results: List[Union[NameSchema, AttributeSchema]] = []

    if isinstance(Schema, (ast.Name, ast.Attribute)):
        # Base case: If we find a name or attribute, extract it and add to
        # results.
        extracted_Schema = extract_name_or_attribute(Schema)
        if extracted_Schema:
            results.append(extracted_Schema)
    elif isinstance(Schema, ast.Subscript):
        # Only process the slice (inner types), not the value (e.g., 'Dict')
        results.extend(extract_inner_types(Schema.slice))
    elif isinstance(Schema, (ast.Tuple, ast.List)):
        # Recursive case: For (str, int), iterate and extract from each
        # element.
        for element in Schema.elts:
            results.extend(extract_inner_types(element))
    elif isinstance(Schema, ast.BinOp) and isinstance(Schema.op, ast.BitOr):
        # Recursive case: For str | int, extract from 'str' and from 'int'.
        results.extend(extract_inner_types(Schema.left))
        results.extend(extract_inner_types(Schema.right))

    return results


def extract_annotation(
    Schema: ast.AST
) -> Union[NameSchema, AttributeSchema, SubscriptSchema, str]:
    """
    Extracts an annotation with a preference for structured Schemas.
    - Returns NameSchema/AttributeSchema for simple types.
    - Returns SubscriptSchema for complex generic types (e.g., List[...]).
    - Falls back to a string for forward references or other unsupported types.
    """
    # Path 1: Handle simple cases like `int` or `models.User` first.
    if isinstance(Schema, (ast.Name, ast.Attribute)):
        return extract_name_or_attribute(Schema)

    # Path 2: Handle complex subscripted types like `List[int]`.
    if isinstance(Schema, ast.Subscript):
        full_type_string = annotation_to_string(Schema)
        inner_types = extract_inner_types(Schema)

        return SubscriptSchema(
            full_str=full_type_string,
            elements=inner_types,
            position=extract_position(Schema)
        )

    # Path 3: Fallback for everything else (forward refs, complex unions,
    # etc.).
    # The full string representation is the most reliable output.
    return annotation_to_string(Schema)


def extract_value(Schema: ast.AST) -> List[Union["NameSchema", "AttributeSchema"]]:
    """Recursively extract NameSchema or AttributeSchema(s) from an AST Schema.

    - Handles Tuple, List, Set (anything with `.elts`).
    - Recursively descends into nested structures.
    - Always returns a list (possibly empty).
    - Filters out None values.
    """
    results: List[Union["NameSchema", "AttributeSchema"]] = []

    if hasattr(Schema, "elts"):  # Tuple, List, Set, etc.
        for elt in Schema.elts:
            results.extend(extract_value(elt))  # recursive call
    else:
        if (extracted := extract_name_or_attribute(Schema)) is not None:
            results.append(extracted)

    return results


def extract_name_or_attribute(
    Schema: ast.AST
) -> Optional[Union[NameSchema, AttributeSchema]]:
    """Extract name or attribute Schemas, handle nested calls like super()"""
    if isinstance(Schema, ast.Name):
        return NameSchema(name=Schema.id, position=extract_position(Schema))
    elif isinstance(Schema, ast.Attribute):
        # Handle cases like super().method() where value might be a Call
        if isinstance(Schema.value, ast.Call):
            # For super().method(), we want to extract the Call as the value
            # Check if it's a super() call
            if (isinstance(Schema.value.func, ast.Name) and
                    Schema.value.func.id == 'super'):
                # Create a special NameSchema for super() calls
                super_Schema = NameSchema(
                    name='super',
                    position=extract_position(Schema.value.func)
                )
                return AttributeSchema(
                    name=Schema.attr,
                    value=super_Schema,
                    position=extract_position(Schema)
                )
            else:
                # For other call().method() patterns, try to extract recursively
                call_value = extract_name_or_attribute(Schema.value.func)
                return AttributeSchema(
                    name=Schema.attr,
                    value=call_value,
                    position=extract_position(Schema)
                )
        else:
            # Normal attribute access like obj.attr
            value = extract_name_or_attribute(Schema.value)
            return AttributeSchema(
                name=Schema.attr,
                value=value,
                position=extract_position(Schema)
            )
    return None


def annotation_to_string(Schema: ast.AST) -> str:
    """Convert annotation to string - focused on type references"""
    if isinstance(Schema, ast.Name):
        return Schema.id
    elif isinstance(Schema, ast.Subscript):
        value = annotation_to_string(Schema.value)
        slice_str = annotation_to_string(Schema.slice)
        return f"{value}[{slice_str}]"
    elif isinstance(Schema, ast.Tuple):
        elements = [annotation_to_string(elt) for elt in Schema.elts]
        return ", ".join(elements)
    elif isinstance(Schema, ast.Constant):
        if isinstance(Schema.value, str):
            return f"'{Schema.value}'"
        return str(Schema.value)
    elif isinstance(Schema, ast.Attribute):
        value = annotation_to_string(Schema.value)
        return f"{value}.{Schema.attr}"
    elif isinstance(Schema, ast.List):
        elements = [annotation_to_string(elt) for elt in Schema.elts]
        return f"[{', '.join(elements)}]"
    elif isinstance(Schema, ast.BinOp) and isinstance(Schema.op, ast.BitOr):
        left = annotation_to_string(Schema.left)
        right = annotation_to_string(Schema.right)
        return f"{left} | {right}"
    else:
        return f"<{type(Schema).__name__}>"
