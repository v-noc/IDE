import ast
from typing import Optional, List
from app.models.properties import TypeKeyValuesProperties
from app.models.node import NodePosition
from app.core.code_elements import Function, Class
from app.db import collections as db
from .visitor_context import VisitorContext


class TypeInferenceVisitor(ast.NodeVisitor):
    """
    A visitor to perform comprehensive type inference for functions and 
    classes.
    
    This visitor:
    1. Extracts type hints from function signatures and return annotations
    2. Infers types from assignments and class attributes
    3. Links to custom class nodes when types refer to them
    4. Uses add_input/add_output methods for functions
    5. Uses add_field method for classes
    """
    
    def __init__(self, context: VisitorContext):
        self.context = context
        self.current_class_stack: List[str] = []  # Track nested classes
        self.current_function_id: Optional[str] = None
        self.builtin_types = {
            'int', 'float', 'str', 'bool', 'list', 'dict', 'tuple', 'set',
            'bytes', 'bytearray', 'complex', 'frozenset', 'range', 'slice',
            'None', 'Any', 'Optional', 'Union', 'List', 'Dict', 'Tuple',
            'Set', 'FrozenSet', 'Callable'
        }

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Process function definitions to extract type information."""
        # Build function qname
        file_qname = self._get_file_qname_from_context()
        if self.current_class_stack:
            class_path = ".".join(self.current_class_stack)
            function_qname = f"{file_qname}.{class_path}.{node.name}"
        else:
            function_qname = f"{file_qname}.{node.name}"
        
        # Get function ID from symbol table
        function_id = self.context.symbol_table.get_symbol_id(function_qname)
        if not function_id:
            return
        
        # Get the Function domain object
        function_node = db.nodes.get(function_id)
        if not function_node:
            return
            
        function_obj = Function(function_node)
        
        # Store current function context
        previous_function_id = self.current_function_id
        self.current_function_id = function_id
        
        # Process function parameters
        self._process_function_parameters(node, function_obj)
        
        # Process return type annotation
        self._process_function_return_type(node, function_obj)
        
        # Visit function body to infer additional types from assignments and returns
        self.generic_visit(node)
        
        # Restore previous function context
        self.current_function_id = previous_function_id

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Process class definitions to extract field type information."""
        # Build class qname
        file_qname = self._get_file_qname_from_context()
        if self.current_class_stack:
            class_path = ".".join(self.current_class_stack)
            class_qname = f"{file_qname}.{class_path}.{node.name}"
        else:
            class_qname = f"{file_qname}.{node.name}"
        
        # Add to class stack for nested classes
        self.current_class_stack.append(node.name)
        
        # Get class ID from symbol table
        class_id = self.context.symbol_table.get_symbol_id(class_qname)
        if class_id:
            # Get the Class domain object
            class_node = db.nodes.get(class_id)
            if class_node:
                class_obj = Class(class_node)
                
                # Process class attributes and type annotations
                self._process_class_attributes(node, class_obj)
        
        # Visit class body
        self.generic_visit(node)
        
        # Remove from class stack
        self.current_class_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        """
        Infers the type of the variable being assigned the result of a call.
        This is crucial for tracking class instantiations.
        """
        # We need to find the assignment this call is part of.
        # This requires navigating up the AST, which is not directly
        # supported by NodeVisitor. A parent-tracking visitor is needed.
        # For now, we will handle this in visit_Assign.
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Process annotated assignments for type information."""
        if isinstance(node.target, ast.Name):
            var_name = node.target.id
            type_str = self._ast_to_string(node.annotation)
           
            position = self._get_node_position(node)
            
            # If we're in a class (not in a method), this is a class attribute
            if (self.current_class_stack and
                    self.current_function_id is None):
                
                # Get current class
                file_qname = self._get_file_qname_from_context()
                class_path = ".".join(self.current_class_stack)
                class_qname = f"{file_qname}.{class_path}"
                
                class_id = self.context.symbol_table.get_symbol_id(class_qname)
                if class_id:
                    class_node = db.nodes.get(class_id)
                    if class_node:
                        class_obj = Class(class_node)
                        
                        # Create field with type information
                        field = TypeKeyValuesProperties(
                            varname=var_name,
                            varType=type_str,
                            position=position
                        )
                        
                        # Link to custom type if it's a local class
                        self._link_custom_type(type_str, field)
                        
                        class_obj.add_field(field)
        
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Process assignments to infer types when no annotation is present."""
        if isinstance(node.value, ast.Call):
            # This is an assignment from a call, e.g., `app = MainApp()`
            inferred_type = self._infer_type_from_value(node.value)
            if inferred_type:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        # Store the inferred type in the context
                        self.context.local_variable_types[var_name] = inferred_type

        # Try to infer type from the value
        if node.value:
            inferred_type = self._infer_type_from_value(node.value)
            
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                 
                    position = self._get_node_position(node)
                    
                    # If we're in a class (not in method), class attribute
                    if (self.current_class_stack and
                            self.current_function_id is None and
                            inferred_type):
                        
                        # Get current class
                        file_qname = self._get_file_qname_from_context()
                        class_path = ".".join(self.current_class_stack)
                        class_qname = f"{file_qname}.{class_path}"
                        
                        class_id = self.context.symbol_table.get_symbol_id(
                            class_qname
                        )
                        if class_id:
                            class_node = db.nodes.get(class_id)
                            if class_node:
                                class_obj = Class(class_node)
                                
                                # Create field with inferred type
                                field = TypeKeyValuesProperties(
                                    varname=var_name,
                                    varType=inferred_type,
                                    position=position
                                )
                                
                                # Link to custom type if it's a local class
                                self._link_custom_type(inferred_type, field)
                                
                                class_obj.add_field(field)
                    else:
                        # Store local variable type if we're not in a class
                        if inferred_type:
                            self.context.local_variable_types[var_name] = inferred_type
        
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        """Process return statements to infer return types."""
        if (node.value and
                self.current_function_id):
            
            inferred_type = self._infer_type_from_value(node.value)
            if inferred_type:
                # Get the Function domain object
                function_node = db.nodes.get(self.current_function_id)
                if function_node:
                    function_obj = Function(function_node)
                    position = self._get_node_position(node)
                    
                    # Check if we already have return type information
                    existing_outputs = function_obj.outputs
                    has_return_type = any(
                        output.varname == "return"
                        for output in existing_outputs
                    )
                    
                    if not has_return_type:
                        # Create output with inferred type
                        output = TypeKeyValuesProperties(
                            varname="return",
                            varType=inferred_type,
                            position=position
                        )
                        
                        # Link to custom type if it's a local class
                        self._link_custom_type(inferred_type, output)
                        
                        function_obj.add_output(output)
        
        self.generic_visit(node)

    def _process_function_parameters(
        self, node: ast.FunctionDef, function_obj: Function
    ) -> None:
        """Extract type information from function parameters."""
        for arg in node.args.args:
            # Skip 'self' parameter
            if arg.arg == 'self':
                # In a method, 'self' refers to an instance of the class.
                # We can use this to infer the class type.
                if self.current_class_stack:
                    file_qname = self._get_file_qname_from_context()
                    class_path = ".".join(self.current_class_stack)
                    class_qname = f"{file_qname}.{class_path}"
                    # Here we could store that 'self' is of type 
                    # 'class_qname'
                    # self.context.set_local_variable_type(
                    #     'self', class_qname
                    # )
                continue
                
            param_name = arg.arg
            type_str = "Any"  # Default type
            
            # Check for type annotation
            if arg.annotation:
                type_str = self._ast_to_string(arg.annotation)
            
            position = self._get_node_position(arg)
            
            # Create input parameter
            input_param = TypeKeyValuesProperties(
                varname=param_name,
                varType=type_str,
                position=position
            )
            
            # Link to custom type if it's a local class
            self._link_custom_type(type_str, input_param)
            
            function_obj.add_input(input_param)

    def _process_function_return_type(self, node: ast.FunctionDef, function_obj: Function) -> None:
        """Extract return type information from function signature."""
        if node.returns:
            return_type = self._ast_to_string(node.returns)
            position = self._get_node_position(node.returns)
            
            # Create output parameter
            output_param = TypeKeyValuesProperties(
                varname="return",
                varType=return_type,
                position=position
            )
            
            # Link to custom type if it's a local class
            self._link_custom_type(return_type, output_param)
            
            function_obj.add_output(output_param)

    def _process_class_attributes(self, node: ast.ClassDef, class_obj: Class) -> None:
        """Extract type information from class attributes and annotations."""
        for item in node.body:
            if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                # Annotated class attribute
                var_name = item.target.id
                type_str = self._ast_to_string(item.annotation)
                position = self._get_node_position(item)
                
                field = TypeKeyValuesProperties(
                    varname=var_name,
                    varType=type_str,
                    position=position
                )
                
                # Link to custom type if it's a local class
                self._link_custom_type(type_str, field)
                
                class_obj.add_field(field)
            
            elif isinstance(item, ast.Assign):
                # Regular assignment in class body
                inferred_type = self._infer_type_from_value(item.value)
                if inferred_type:
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            position = self._get_node_position(item)
                            
                            field = TypeKeyValuesProperties(
                                varname=var_name,
                                varType=inferred_type,
                                position=position
                            )
                            
                            # Link to custom type if it's a local class
                            self._link_custom_type(inferred_type, field)
                            
                            class_obj.add_field(field)

    def _link_custom_type(self, type_str: str, type_property: TypeKeyValuesProperties) -> None:
        """Link to custom class nodes when types refer to them."""
        # Clean up the type string (remove Optional, List, etc. wrappers)
        clean_type = self._extract_base_type(type_str)
        
        if clean_type and clean_type not in self.builtin_types:
            # Check if this refers to a local class
            if self.context.symbol_table.is_local_module(clean_type):
                # Try to find the class node
                class_id = self.context.symbol_table.get_symbol_id(clean_type)
                if class_id:
                    # This could be enhanced to create a proper relationship edge
                    # For now, we store the link information in the type string
                    type_property.varType = f"{type_str}[{class_id}]"
            else:
                # External type - check if we need to create a package reference
                package_parts = clean_type.split('.')
                if len(package_parts) > 1:
                    package_name = package_parts[0]
                    package_id = self.context.symbol_table.get_or_create_package_id(package_name)
                    # Store package link information
                    type_property.varType = f"{type_str}<{package_id}>"

    def _extract_base_type(self, type_str: str) -> Optional[str]:
        """Extract the base type from complex type annotations."""
        # Handle common generic types
        if type_str.startswith('Optional[') and type_str.endswith(']'):
            inner = type_str[9:-1]  # Remove 'Optional[' and ']'
            return self._extract_base_type(inner)
        
        if type_str.startswith('List[') and type_str.endswith(']'):
            inner = type_str[5:-1]  # Remove 'List[' and ']'
            return self._extract_base_type(inner)
        
        if type_str.startswith('Dict[') and type_str.endswith(']'):
            # For Dict[K, V], we could extract both types, but for now 
            # just return None
            return None
        
        if type_str.startswith('Union[') and type_str.endswith(']'):
            # For Union types, this is complex - for now just return None
            return None
        
        # Clean up any remaining brackets or whitespace
        clean_type = type_str.strip()
        if clean_type:
            return clean_type
        
        return None

    def _infer_type_from_value(self, value_node: ast.AST) -> Optional[str]:
        """Infer type from an AST value node."""
        if isinstance(value_node, ast.Constant):
            if isinstance(value_node.value, int):
                return "int"
            elif isinstance(value_node.value, float):
                return "float"
            elif isinstance(value_node.value, str):
                return "str"
            elif isinstance(value_node.value, bool):
                return "bool"
            elif value_node.value is None:
                return "None"
        
        elif isinstance(value_node, ast.List):
            return "list"
        elif isinstance(value_node, ast.Dict):
            return "dict"
        elif isinstance(value_node, ast.Tuple):
            return "tuple"
        elif isinstance(value_node, ast.Set):
            return "set"
        
        elif isinstance(value_node, ast.Call):
            # Try to infer type from constructor calls
            if isinstance(value_node.func, ast.Name):
                func_name = value_node.func.id
                
                # Check if it's a local class (constructor call)
                file_qname = self._get_file_qname_from_context()
                local_class_qname = f"{file_qname}.{func_name}"
                if self.context.symbol_table.get_symbol_id(local_class_qname):
                    return local_class_qname
                
                # Check if it's just the class name without file prefix
                if self.context.symbol_table.get_symbol_id(func_name):
                    return func_name
                
                # Check builtin types
                if func_name in self.builtin_types:
                    return func_name
        
        elif isinstance(value_node, ast.Name):
            # Variable reference - look up its type if we tracked it
            var_name = value_node.id
            if var_name in self.context.local_variable_types:
                return self.context.local_variable_types[var_name]
            return None
        
        return None

    def _ast_to_string(self, node: ast.AST) -> str:
        """Convert an AST node to its string representation."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._ast_to_string(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._ast_to_string(node.value)}[{self._ast_to_string(node.slice)}]"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif hasattr(ast, 'unparse'):  # Python 3.9+
            return ast.unparse(node)
        else:
            # Fallback for older Python versions
            return str(node.__class__.__name__)

    def _get_node_position(self, node: ast.AST) -> NodePosition:
        """Extract position information from an AST node."""
        return NodePosition(
            col_offset=getattr(node, 'col_offset', 0),
            end_line_no=getattr(
                node, 'end_lineno', getattr(node, 'lineno', 0)
            ),
            line_no=getattr(node, 'lineno', 0),
            end_col_offset=getattr(
                node, 'end_col_offset', getattr(node, 'col_offset', 0)
            )
        )

    def _get_file_qname_from_context(self) -> str:
        """Get the file's qualified name from the context."""
        # Get file node from database
        file_node = db.nodes.get(self.context.file_id)
        if file_node:
            return file_node.qname
        return "unknown_file"
