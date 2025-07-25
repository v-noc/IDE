"""
Tree building utilities for creating hierarchical structures from file paths.
"""
import os
from typing import Dict, Any, List


def build_tree_from_paths(
    paths: List[str], base_path: str = ""
) -> Dict[str, Any]:
    """
    Builds a nested dictionary tree structure from a list of file paths.
    
    Args:
        paths: List of absolute file paths
        base_path: Base path to remove from each path (optional)
        
    Returns:
        Nested dictionary where folders are dicts and files are None values
        
    Example:
        paths = ["/project/src/main.py", "/project/src/utils/helper.py"]
        base_path = "/project"
        
        Returns:
        {
            "src": {
                "main.py": None,
                "utils": {
                    "helper.py": None
                }
            }
        }
    """
    tree = {}
    
    for path in paths:
        # Remove base path prefix and clean the path
        if base_path:
            relative_path = path.replace(base_path, "").lstrip("/")
        else:
            relative_path = path.lstrip("/")
            
        if not relative_path:
            continue
            
        parts = relative_path.split("/")
        current = tree
        
        for i, part in enumerate(parts):
            if i == len(parts) - 1:  # It's a file
                current.setdefault(part, None)
            else:  # It's a folder
                current = current.setdefault(part, {})
                
    return tree


def print_tree(tree: Dict[str, Any], indent: int = 0) -> None:
    """
    Pretty prints a tree structure for debugging purposes.
    
    Args:
        tree: The tree dictionary to print
        indent: Current indentation level
    """
    for name, subtree in tree.items():
        print("  " * indent + name)
        if subtree is not None:
            print_tree(subtree, indent + 1)


def get_tree_paths(tree: Dict[str, Any], base_path: str = "") -> List[str]:
    """
    Extracts all file paths from a tree structure.
    
    Args:
        tree: The tree dictionary
        base_path: Base path to prepend to each path
        
    Returns:
        List of all file paths in the tree
    """
    paths = []
    
    for name, subtree in tree.items():
        current_path = os.path.join(base_path, name) if base_path else name
        
        if subtree is None:  # It's a file
            paths.append(current_path)
        else:  # It's a folder
            paths.extend(get_tree_paths(subtree, current_path))
            
    return paths


def get_tree_folders(tree: Dict[str, Any], base_path: str = "") -> List[str]:
    """
    Extracts all folder paths from a tree structure.
    
    Args:
        tree: The tree dictionary
        base_path: Base path to prepend to each path
        
    Returns:
        List of all folder paths in the tree
    """
    folders = []
    
    for name, subtree in tree.items():
        current_path = os.path.join(base_path, name) if base_path else name
        
        if subtree is not None:  # It's a folder
            folders.append(current_path)
            folders.extend(get_tree_folders(subtree, current_path))
            
    return folders 