# src/backend/app/core/parser/python/symbol_table.py
from typing import Dict, List, Optional


class SymbolTable:
    """
    The central component for resolving names, types, and dependencies.
    It acts as a stateful, in-memory cache and resolution engine that sits
    in front of the ArangoDB database.
    """
    def __init__(self):
        self._qname_to_id: Dict[str, str] = {}
        self._file_id_to_imports: Dict[str, Dict[str, str]] = {}
        self._package_table: Dict[str, str] = {}
        self._scope_stack: List[str] = []
        # Type information cache
        self._function_return_types: Dict[str, str] = {}
        self._variable_types: Dict[str, str] = {}  # file_id:var_name -> type

    def add_symbol(self, qname: str, db_id: str) -> None:
        """Caches a symbol's qname and its database ID."""
        self._qname_to_id[qname] = db_id

    def add_import(self, file_id: str, alias: str, qname: str) -> None:
        """
        Registers an import statement for a specific file.
        
        Args:
            file_id: The database ID of the file containing the import
            alias: The name used to reference the import 
                  (e.g., 'np' for 'import numpy as np')
            qname: The fully qualified name of the imported symbol 
                   (e.g., 'numpy')
        """
        if file_id not in self._file_id_to_imports:
            self._file_id_to_imports[file_id] = {}
        
        self._file_id_to_imports[file_id][alias] = qname
    
    def resolve_import_qname(self, file_id: str, name: str) -> Optional[str]:
        """
        Resolves an imported name to its fully qualified name and determines
        if it's a local module or external package.
        
        Args:
            file_id: The database ID of the file where the name is being used
            name: The name being referenced (e.g., 'Request', 'np')
            
        Returns:
            The fully qualified name if the name is an import, None otherwise
        """
        # Check if this file has any imports
        if file_id not in self._file_id_to_imports:
            return None
        
        # Look up the alias in the file's import map
        file_imports = self._file_id_to_imports[file_id]
        if name not in file_imports:
            return None
            
        return file_imports[name]
    
    def is_local_module(self, qname: str) -> bool:
        """
        Determines if a qname refers to a local module or an external package.
        
        Args:
            qname: The fully qualified name to check
            
        Returns:
            True if it's a local module, False if it's an external package
        """
        # Check if the qname (or any prefix of it) exists in our known symbols
        # For example, if we're checking 'myproject.utils.helper', we check:
        # 1. 'myproject.utils.helper' (exact match)
        # 2. 'myproject.utils' (module containing the symbol)
        # 3. 'myproject' (parent module)
        
        # First check exact match
        # if qname in self._qname_to_id:
        #     return True
        
        # Then check prefixes (for cases like myproject.utils.function_name)
        parts = qname.split('.')
        for i in range(len(parts)):
            prefix = '.'.join(parts[:i+1])
            if prefix in self._qname_to_id:
                return True
        
        # Check if any known qname starts with this qname as a prefix
        # This handles cases where we're importing a module that contains 
        # other modules we know about
        for known_qname in self._qname_to_id.keys():
            if known_qname.startswith(qname + '.'):
                return True
        
        return False
    
    def get_or_create_package_id(self, package_qname: str) -> str:
        """
        Gets the database ID for a package, or marks it for creation if it 
        doesn't exist.
        
        This method is used during the dependency resolution phase to handle
        external packages that need PackageNode creation.
        
        Args:
            package_qname: The fully qualified name of the package
            
        Returns:
            The database ID of the package (existing or placeholder 
            for creation)
        """
        # Check if we already have this package
        if package_qname in self._qname_to_id:
            return self._qname_to_id[package_qname]
        
        # Create a placeholder ID that will be resolved during scanning
        placeholder_id = f"package_{package_qname.replace('.', '_')}"
        self._qname_to_id[package_qname] = placeholder_id
        
        return placeholder_id
    
    def get_symbol_id(self, qname: str) -> Optional[str]:
        """
        Gets the database ID for a symbol by its qname.
        
        Args:
            qname: The fully qualified name of the symbol
            
        Returns:
            The database ID if found, None otherwise
        """
        return self._qname_to_id.get(qname)
    
    def get_file_imports(self, file_id: str) -> Dict[str, str]:
        """
        Gets all imports for a specific file.
        
        Args:
            file_id: The database ID of the file
            
        Returns:
            Dictionary mapping alias names to their fully qualified names
        """
        return self._file_id_to_imports.get(file_id, {})
    
    def push_scope(self, scope_id: str) -> None:
        """
        Pushes a new scope onto the scope stack.
        To be implemented in Phase 4 for type inference.
        """
        self._scope_stack.append(scope_id)

    def pop_scope(self) -> Optional[str]:
        """
        Pops the current scope from the scope stack.
        To be implemented in Phase 4 for type inference.
        """
        if self._scope_stack:
            return self._scope_stack.pop()
        return None

    def resolve_call_target_to_id(
        self, call_node, scope_id: str
    ) -> Optional[str]:
        """
        Resolves a function call to its target function's database ID.
        To be implemented in Phase 4 for call resolution with type
        inference.
        """
        # To be implemented in Phase 4
        pass
    
    def clear_file_imports(self, file_id: str) -> None:
        """
        Clears all imports for a specific file.
        Useful for re-processing files during development.
        
        Args:
            file_id: The database ID of the file
        """
        if file_id in self._file_id_to_imports:
            del self._file_id_to_imports[file_id]
    
    def get_all_local_modules(self) -> List[str]:
        """
        Gets all known local module qnames.
        
        Returns:
            List of all local module qualified names
        """
        return list(self._qname_to_id.keys())

    def get_all_packages(self) -> Dict[str, str]:
        """
        Gets all known package qnames and their IDs for debugging.
        
        Returns:
            Dictionary mapping package qnames to their database IDs
        """
        packages = {}
        for qname, node_id in self._qname_to_id.items():
            # Simple heuristic: if it's not a file path, it might be a package
            if '/' not in qname and not qname.startswith('nodes/'):
                packages[qname] = node_id
        return packages

    # === NEW TYPE INFERENCE METHODS ===
    
    def set_function_return_type(self, function_qname: str, return_type: str) -> None:
        """
        Caches the return type of a function for type inference.
        
        Args:
            function_qname: The fully qualified name of the function
            return_type: The return type string
        """
        self._function_return_types[function_qname] = return_type
    
    def get_function_return_type(self, function_qname: str) -> Optional[str]:
        """
        Gets the cached return type of a function.
        
        Args:
            function_qname: The fully qualified name of the function
            
        Returns:
            The return type string if known, None otherwise
        """
        return self._function_return_types.get(function_qname)
    
    def set_variable_type(self, file_id: str, variable_name: str, var_type: str) -> None:
        """
        Caches the type of a variable within a file scope.
        
        Args:
            file_id: The database ID of the file
            variable_name: The name of the variable
            var_type: The type string
        """
        key = f"{file_id}:{variable_name}"
        self._variable_types[key] = var_type
    
    def get_variable_type(self, file_id: str, variable_name: str) -> Optional[str]:
        """
        Gets the cached type of a variable within a file scope.
        
        Args:
            file_id: The database ID of the file
            variable_name: The name of the variable
            
        Returns:
            The type string if known, None otherwise
        """
        key = f"{file_id}:{variable_name}"
        return self._variable_types.get(key)
    
    def resolve_call_type(
        self, 
        file_id: str, 
        call_target: str, 
        call_type: str = "function"
    ) -> Optional[str]:
        """
        Resolves the return type of a function call.
        
        Args:
            file_id: The database ID of the file where the call is made
            call_target: The name of the function/method being called
            call_type: Type of call ("function", "method", "constructor")
            
        Returns:
            The expected return type if it can be resolved, None otherwise
        """
        # First, try to resolve as an import
        import_qname = self.resolve_import_qname(file_id, call_target)
        if import_qname:
            # Check if we have type information for this imported function
            return self.get_function_return_type(import_qname)
        
        # Try to resolve as a local function
        # This requires building the qname from the current file context
        file_node_id = file_id  # Simplified for now
        
        # Check if it's a local function call
        if self.is_local_module(call_target):
            return self.get_function_return_type(call_target)
        
        # For method calls, this would need more sophisticated resolution
        # involving object types and class hierarchies
        
        return None
    
    def infer_assignment_type(
        self, 
        file_id: str, 
        assignment_value: str, 
        assignment_type: str = "call"
    ) -> Optional[str]:
        """
        Infers the type of an assignment based on its value.
        
        Args:
            file_id: The database ID of the file
            assignment_value: The value being assigned (function name, etc.)
            assignment_type: Type of assignment ("call", "literal", "variable")
            
        Returns:
            The inferred type if possible, None otherwise
        """
        if assignment_type == "call":
            return self.resolve_call_type(file_id, assignment_value)
        elif assignment_type == "variable":
            return self.get_variable_type(file_id, assignment_value)
        # For literals, the type inference visitor handles this directly
        return None

    def debug_symbol_table(self) -> None:
        """
        Prints the current state of the symbol table for debugging.
        """
        print("=== Symbol Table Debug ===")
        print(f"Total symbols: {len(self._qname_to_id)}")
        
        packages = self.get_all_packages()
        print(f"Packages ({len(packages)}):")
        for qname, node_id in packages.items():
            print(f"  {qname} -> {node_id}")
        
        print(f"File imports: {len(self._file_id_to_imports)}")
        for file_id, imports in self._file_id_to_imports.items():
            print(f"  {file_id}: {imports}")
        
        print(f"Function return types: {len(self._function_return_types)}")
        for func_qname, return_type in self._function_return_types.items():
            print(f"  {func_qname} -> {return_type}")
        
        print(f"Variable types: {len(self._variable_types)}")
        for var_key, var_type in self._variable_types.items():
            print(f"  {var_key} -> {var_type}")
        print("=========================")
