# Import analysis and resolution tests
import pytest
from app.core.parser.project_scanner import ProjectScanner
from app.db import collections

# Marks all tests in this file as using the 'clear_db' fixture
pytestmark = pytest.mark.usefixtures("clear_db")


def test_import_position_tracking(complex_project_path):
    """
    Test that import positions are correctly tracked and recorded.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Get all import edges
    import_edges = collections.uses_import_edges.find({})
    
    # Verify import positions are tracked
    for edge in import_edges:
        assert hasattr(edge, 'import_position')
        assert edge.import_position.line_no > 0
        assert edge.import_position.col_offset >= 0
    
    # Find specific import (e.g., "from typing import Dict, List, Optional")
    typing_imports = [
        edge for edge in import_edges 
        if 'typing' in edge.target_qname
    ]
    assert len(typing_imports) > 0, "Should find typing imports"
    
    # Check that typing imports are at the top of files (low line numbers)
    for edge in typing_imports:
        assert edge.import_position.line_no < 15, (
            "Typing imports should be near top of file"
        )


def test_aliased_imports_resolution(complex_project_path):
    """
    Test that aliased imports (import X as Y) are correctly handled.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    # Find aliased import edges
    aliased_edges = collections.uses_import_edges.find({})
    
    # Look for specific aliases like "import json as JSON"
    json_alias_edges = [
        edge for edge in aliased_edges 
        if edge.alias == "JSON" and "json" in edge.target_qname
    ]
    assert len(json_alias_edges) > 0, "Should find JSON alias import"
    
    # Look for "from .utils.math_utils import calculate as calc"
    calc_alias_edges = [
        edge for edge in aliased_edges 
        if edge.alias == "calc" 
    ]
    assert len(calc_alias_edges) > 0, "Should find calc alias import"
    
    # Look for "import logging as log"
    log_alias_edges = [
        edge for edge in aliased_edges 
        if edge.alias == "log" and "logging" in edge.target_qname
    ]
    assert len(log_alias_edges) > 0, "Should find log alias import"


def test_relative_imports_handling(complex_project_path):
    """
    Test that relative imports (from . import, from .. import) are handled.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    import_edges = collections.uses_import_edges.find({})
    
    # Look for relative imports like "from . import config"
    relative_imports = [
        edge for edge in import_edges 
        if 'config' in edge.target_qname
    ]
    assert len(relative_imports) > 0, (
        "Should find relative imports to config"
    )
    
    # Look for "from .models.user import User, UserType"
    user_imports = [
        edge for edge in import_edges 
        if 'models.user.User' in edge.target_qname
    ]
    assert len(user_imports) > 0, "Should find User imports"


def test_position_accuracy_for_imports(complex_project_path):
    """
    Test that import positions are accurate for different import styles.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    import_edges = collections.uses_import_edges.find({})
    
    # Group imports by line number to test positioning
    line_positions = {}
    for edge in import_edges:
        line_no = edge.import_position.line_no
        if line_no not in line_positions:
            line_positions[line_no] = []
        line_positions[line_no].append(edge)
    
    # Verify that imports are generally at the top of files
    early_imports = [
        edge for edge in import_edges 
        if edge.import_position.line_no <= 20
    ]
    assert len(early_imports) > 0, (
        "Should find imports near the top of files"
    )
    
    # Test that column offsets are reasonable
    for edge in import_edges:
        col_offset = edge.import_position.col_offset
        target_qname = edge.target_qname
        assert 0 <= col_offset <= 100, (
            f"Column offset should be reasonable for {target_qname}"
        )


def test_complex_project_import_patterns(complex_project_path):
    """
    Test various import patterns in the complex project.
    """
    scanner = ProjectScanner(str(complex_project_path))
    scanner.scan()
    
    import_edges = collections.uses_import_edges.find({})
    
    # Test different import types exist
    import_types = {
        'standard_library': False,  # os, sys, json
        'relative': False,          # from . import, from .module import
        'aliased': False,           # import X as Y
        'from_import': False,       # from X import Y
    }
    
    for edge in import_edges:
        target = edge.target_qname
        alias = edge.alias
        
        # Check for standard library
        if any(lib in target for lib in ['os', 'sys', 'json', 'typing']):
            import_types['standard_library'] = True
        
        # Check for relative imports (would contain project modules)
        if any(mod in target for mod in ['config', 'utils', 'models']):
            import_types['relative'] = True
            
        # Check for aliases
        if alias and alias != target.split('.')[-1]:
            import_types['aliased'] = True
            
        # Most imports are from_import style in our test project
        import_types['from_import'] = True
    
    # Verify we found various import patterns
    assert import_types['standard_library'], (
        "Should find standard library imports"
    )
    assert import_types['relative'], "Should find relative imports"
    assert import_types['aliased'], "Should find aliased imports" 