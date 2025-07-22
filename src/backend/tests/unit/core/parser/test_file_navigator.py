import os
import shutil
import pytest
from app.core.parser.file_navigator import FileNavigator
from pathlib import Path

def test_file_navigator_finds_python_files():
    path = Path(__file__).parent
    sample_project_path = path / "advanced_example"
    navigator = FileNavigator(sample_project_path.resolve(), "v-noc.toml")
    python_files = list(navigator.find_files(extensions=['.py']))
    print(python_files)
    assert len(python_files) == 3
    
    file_names = [os.path.basename(p) for p in python_files]
    assert "main.py" in file_names
    assert "utils.py" in file_names
    assert "main.py" in file_names
