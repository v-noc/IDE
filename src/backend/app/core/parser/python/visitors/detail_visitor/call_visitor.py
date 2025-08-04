import ast
from typing import Optional, Dict
import astpretty as asp
from app.models.edges import CallEdge
from app.models.node import NodePosition
from .visitor_context import VisitorContext


class CallVisitor(ast.NodeVisitor):
    """
    A visitor to resolve all function/method calls and create CallEdges.
    """
    def __init__(self, context: VisitorContext):
        self.context = context
        self.current_caller_id: Optional[str] = None
        self.call_order_counter: Dict[str, int] = {}  # Track order per caller
        self.class_stack: list[str] = []  # Track nested classes

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Sets the context for which function is making the calls.
        This determines the 'from' part of CallEdge.
        """
        # Build the function qname from file context and class hierarchy
        file_qname = self._get_file_qname_from_context()
        
        if self.class_stack:
            # If we're inside a class, it's a method
            class_path = ".".join(self.class_stack)
            function_qname = f"{file_qname}.{class_path}.{node.name}"
        else:
            # Top-level function
            function_qname = f"{file_qname}.{node.name}"
        
        # Look up the function's database ID from the symbol table
        function_id = self.context.symbol_table.get_symbol_id(function_qname)
        
        if function_id:
            # Store the current caller for nested visits
            previous_caller = self.current_caller_id
            self.current_caller_id = function_id
            
            # Initialize call order counter for this function
            if function_id not in self.call_order_counter:
                self.call_order_counter[function_id] = 0
            
            # Visit the function body to find calls
            self.generic_visit(node)
            
            # Restore previous caller context
            self.current_caller_id = previous_caller

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Tracks class context for method resolution.
        """
        # Push class onto stack
        self.class_stack.append(node.name)
        
        # Visit the class body
        self.generic_visit(node)
        
        # Pop class from stack
        self.class_stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        """
        Resolves a call target and creates a CallEdge.
        """
        if not self.current_caller_id:
            # Skip calls outside of functions
            return
        
        # Get the position of this call
        position = NodePosition(
            line_no=node.lineno,
            col_offset=node.col_offset,
            end_line_no=getattr(node, 'end_lineno', node.lineno),
            end_col_offset=getattr(node, 'end_col_offset', 
                                   node.col_offset + len(str(node.func)))
        )
        
        # Resolve the call target
        target_id = self._resolve_call_target(node)
        
        if target_id:
            # Get the next order number for this caller
            order = self.call_order_counter[self.current_caller_id]
            self.call_order_counter[self.current_caller_id] += 1
            
            # Create the CallEdge
            call_edge = CallEdge(
                from_id=self.current_caller_id,
                to_id=target_id,
                order=order,
                position=position
            )
            
            # Add to results
            self.context.results.append(call_edge)
        
        # Continue visiting child nodes for nested calls
        self.generic_visit(node)

    def _get_file_qname_from_context(self) -> str:
        """
        Gets the file's qualified name from the context.
        """
        # Find the file qname by looking through the symbol table
        for qname, node_id in self.context.symbol_table._qname_to_id.items():
            if node_id == self.context.file_id:
                return qname
        
        # Fallback: construct from file path (this shouldn't happen normally)
        return "unknown_file"

    def _resolve_call_target(self, node: ast.Call) -> Optional[str]:
        """
        Resolves a function call to its target function's database ID.
        
        Args:
            node: The ast.Call node representing the function call
            
        Returns:
            The database ID of the target function/method, or None if not found
        """
        # Handle different types of calls
        if isinstance(node.func, ast.Name):
            # Simple function call: function_name()
            return self._resolve_simple_call(node.func.id)
        
        elif isinstance(node.func, ast.Attribute):
            # Method call: object.method() or module.function()
            return self._resolve_attribute_call(node.func)
        
        return None

    def _resolve_simple_call(self, func_name: str) -> Optional[str]:
        """
        Resolves a simple function call by name.
        
        Args:
            func_name: The name of the function being called
            
        Returns:
            Database ID of the target function or None if not found
        """
        # First, check if it's an imported function
        file_imports = self.context.symbol_table.get_file_imports(
            self.context.file_id
        )
        
        if func_name in file_imports:
            # It's an imported function
            imported_qname = file_imports[func_name]
            return self.context.symbol_table.get_symbol_id(imported_qname)
        
        # Next, check if it's a local function in the same file
        file_qname = self._get_file_qname_from_context()
        local_func_qname = f"{file_qname}.{func_name}"
        target_id = self.context.symbol_table.get_symbol_id(local_func_qname)
        
        if target_id:
            return target_id
        
        # Check if it's a class constructor (instantiation call)
        # Look for classes with the same name
        for qname, node_id in self.context.symbol_table._qname_to_id.items():
            if qname.endswith(f".{func_name}") or qname == func_name:
                # This could be a class - we'll assume it's callable
                return node_id
        
        return None

    def _resolve_attribute_call(
        self, attr_node: ast.Attribute
    ) -> Optional[str]:
        """
        Resolves an attribute call (method or module function call).
        
        Args:
            attr_node: The ast.Attribute node representing the call
            
        Returns:
            Database ID of the target function/method or None if not found
        """
        # This is a complex case that would require type inference
        # For now, we'll handle simple cases like module.function() and 
        # self.method()
        if isinstance(attr_node.value, ast.Name):
            base_name = attr_node.value.id
            method_name = attr_node.attr
            
            # Handle self.method() calls
            if base_name == "self":
                return self._resolve_self_method_call(method_name)
            
            # Check if base_name is a local variable with known type
            if base_name in self.context.local_variable_types:
                var_type = self.context.local_variable_types[base_name]
                return self._resolve_instance_method_call(
                    var_type, method_name
                )
            
            print(asp.pprint(attr_node))
            # Check if base_name is an import
            file_imports = self.context.symbol_table.get_file_imports(
                self.context.file_id
            )
            for file_import in file_imports:
                print(f"file_import: {file_import}")
            if base_name in file_imports:
                # It's a module import, resolve to module.function
                module_qname = file_imports[base_name]
                target_qname = f"{module_qname}.{method_name}"
                print(f"target_qname: {target_qname}")
                id = self.context.symbol_table.get_symbol_id(target_qname)
                for qname, node_id in (
                    self.context.symbol_table._qname_to_id.items()
                ):
                    if "time" in qname:
                        print(f"qname: {qname}")
                        print(f"node_id: {node_id}")
                # Todo : check if the target_qname is a function or a class
                if id:
                    return id
                else:
                    return self.context.symbol_table.get_symbol_id(
                        module_qname
                    )
        
        # For more complex attribute calls (obj.method), we would need
        # type inference to resolve the type of 'obj' first
        # This will be implemented in Phase 4
        
        return None

    def _resolve_instance_method_call(
        self, class_type: str, method_name: str
    ) -> Optional[str]:
        """
        Resolves an instance method call using the known type of the instance.
        
        Args:
            class_type: The type/class name of the instance
            method_name: The name of the method being called
            
        Returns:
            Database ID of the target method or None if not found
        """
        # First, try to find the class in the symbol table
        class_id = self.context.symbol_table.get_symbol_id(class_type)
        if not class_id:
            # Try with file prefix if it's a local class
            file_qname = self._get_file_qname_from_context()
            full_class_qname = f"{file_qname}.{class_type}"
            class_id = self.context.symbol_table.get_symbol_id(
                full_class_qname
            )
            if class_id:
                class_type = full_class_qname
        
        if class_id:
            # Build the method qname: class_qname.method_name
            method_qname = f"{class_type}.{method_name}"
            return self.context.symbol_table.get_symbol_id(method_qname)
        
        return None

    def _resolve_self_method_call(self, method_name: str) -> Optional[str]:
        """
        Resolves a self.method() call to the method in the current class.
        
        Args:
            method_name: The name of the method being called
            
        Returns:
            Database ID of the target method or None if not found
        """
        if not self.class_stack:
            # Not inside a class, self doesn't make sense
            return None
        
        # Build the method qname: file.Class.method
        file_qname = self._get_file_qname_from_context()
        class_path = ".".join(self.class_stack)
        method_qname = f"{file_qname}.{class_path}.{method_name}"
        
        # Look up the method in the symbol table
        return self.context.symbol_table.get_symbol_id(method_qname)
