import pytest

from pathlib import Path

from app.core.parser.graph_builder import GraphBuilder


current_file_path = Path(__file__).resolve()
print("Current file path:", current_file_path)
current_dir = current_file_path.parent
PROJECT_PATH = Path(current_dir, "./sample_project").absolute()


@pytest.fixture()
def create_sample_project(arangodb_client):
    builder = GraphBuilder(
        project_path=PROJECT_PATH.as_posix(),
        ignore_file_name=None,
        db=arangodb_client
    )
    builder.build(
        "Protector", "Protector is a tool for protecting your code.")
