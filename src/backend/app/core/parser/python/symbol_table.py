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
        self._scope_stack: List[str] = []

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
        if qname in self._qname_to_id:
            return True
        
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

    def resolve_call_target_to_id(self, call_node, scope_id: str) -> Optional[str]:
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
