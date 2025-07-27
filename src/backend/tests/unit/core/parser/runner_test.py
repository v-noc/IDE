from app.core.parser.project_scanner import ProjectScanner
from pathlib import Path

def test_debug_project_scanner():
    scanner = ProjectScanner(str(Path(__file__).parent.parent / "sample_project"))
    scanner.scan()
    print(scanner.symbol_table._qname_to_id)

if __name__ == "__main__":
    test_debug_project_scanner()
