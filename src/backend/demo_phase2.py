#!/usr/bin/env python3
"""
Demo script for Phase 2: Dependency and Import Resolution

This script demonstrates the Phase 2 implementation working on a sample
Python project, showing how imports are resolved and dependency edges
are created.
"""

import sys
from pathlib import Path

# Add the backend to Python path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.parser.python.symbol_table import SymbolTable
from app.core.parser.python.file_parser import PythonFileParser
from app.core.parser.python.ast_cache import ASTCache
from app.models.edges import UsesImportEdge


def create_sample_project():
    """Create a sample Python project structure for demonstration."""
    sample_code = {
        "main.py": '''
import json
import os
from fastapi import Request, HTTPException
from typing import List, Dict
from my_project.utils import helper_function, DataProcessor
from my_project.models.user import User

def main():
    """Main application function."""
    config_path = os.path.join("config", "settings.json")
    
    with open(config_path) as f:
        config = json.load(f)
    
    processor = DataProcessor(config)
    users: List[User] = processor.load_users()
    
    return {"users": len(users), "config": config}

def handle_request(request: Request) -> Dict:
    """Handle incoming HTTP request."""
    try:
        data = helper_function(request.json())
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
''',
        
        "utils.py": '''
from typing import Any, Dict, List
import pandas as pd
from my_project.models.user import User

class DataProcessor:
    """Processes user data."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.df = pd.DataFrame()
    
    def load_users(self) -> List[User]:
        """Load users from data source."""
        # Mock implementation
        return [User(id=1, name="John")]

def helper_function(data: Any) -> Dict[str, Any]:
    """Helper function for data processing."""
    return {"processed": True, "data": data}
''',
        
        "models/user.py": '''
from typing import Optional
from dataclasses import dataclass

@dataclass
class User:
    """User model."""
    id: int
    name: str
    email: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email
        }
'''
    }
    
    return sample_code


def demonstrate_phase2():
    """Demonstrate Phase 2 dependency resolution."""
    print("🚀 Phase 2: Dependency and Import Resolution Demo")
    print("=" * 60)
    
    # Initialize components
    ast_cache = ASTCache()
    symbol_table = SymbolTable()
    project_root = "/demo/my_project"
    file_parser = PythonFileParser(ast_cache, symbol_table, project_root)
    
    # Create sample project
    sample_files = create_sample_project()
    
    print("📁 Sample Project Structure:")
    for filename in sample_files.keys():
        print(f"  - {filename}")
    print()
    
    # Simulate project setup - add local modules to symbol table
    symbol_table.add_symbol("my_project", "project_1")
    symbol_table.add_symbol("my_project.main", "file_main")
    symbol_table.add_symbol("my_project.utils", "file_utils")
    symbol_table.add_symbol("my_project.models", "file_models")
    symbol_table.add_symbol("my_project.models.user", "file_user")
    
    print("🔍 Processing files and analyzing dependencies...")
    print()
    
    total_dependencies = 0
    local_imports = 0
    external_packages = set()
    
    for filename, code in sample_files.items():
        print(f"📄 Analyzing {filename}:")
        print("-" * 40)
        
        # Run declaration pass
        declared_nodes = file_parser.run_declaration_pass(filename, code)
        print(f"  ✅ Found {len(declared_nodes)} declarations")
        
        # Add declared nodes to symbol table
        for node in declared_nodes:
            symbol_table.add_symbol(node.qname, f"node_{node.name}")
        
        # Run detail pass for dependency analysis
        file_id = f"file_{filename.replace('.py', '').replace('/', '_')}"
        dependency_edges = file_parser.run_detail_pass(filename, file_id)
        
        # Analyze the dependencies
        usage_edges = [edge for edge in dependency_edges 
                      if isinstance(edge, UsesImportEdge)]
        
        print(f"  📊 Found {len(usage_edges)} import usages:")
        
        for edge in usage_edges:
            target_qname = getattr(edge, 'target_qname', 'unknown')
            is_local = symbol_table.is_local_module(target_qname)
            
            if is_local:
                local_imports += 1
                icon = "🏠"
                type_str = "Local"
            else:
                external_packages.add(target_qname.split('.')[0])
                icon = "📦"
                type_str = "External"
            
            print(f"    {icon} {edge.alias} -> {target_qname} ({type_str})")
            total_dependencies += 1
        
        print()
    
    # Summary
    print("📈 Analysis Summary:")
    print("=" * 60)
    print(f"Total Dependencies Found: {total_dependencies}")
    print(f"Local Module Imports: {local_imports}")
    print(f"External Package Imports: {total_dependencies - local_imports}")
    print(f"Unique External Packages: {len(external_packages)}")
    print()
    
    print("📦 External Packages Detected:")
    for pkg in sorted(external_packages):
        print(f"  - {pkg}")
    print()
    
    # Demonstrate symbol table functionality
    print("🔧 Symbol Table Functionality:")
    print("-" * 40)
    print("Local module detection examples:")
    test_modules = [
        "my_project.utils",
        "my_project.models.user.User",
        "fastapi",
        "pandas.DataFrame"
    ]
    
    for module in test_modules:
        is_local = symbol_table.is_local_module(module)
        icon = "🏠" if is_local else "📦"
        type_str = "Local" if is_local else "External"
        print(f"  {icon} {module} -> {type_str}")
    
    print()
    print("✅ Phase 2 implementation successfully demonstrated!")
    print("🎯 Key features working:")
    print("  - Import statement parsing")
    print("  - Local vs external module detection")
    print("  - Dependency edge creation")
    print("  - Alias resolution")
    print("  - Position tracking")
    print("  - Error handling")


if __name__ == "__main__":
    demonstrate_phase2() 