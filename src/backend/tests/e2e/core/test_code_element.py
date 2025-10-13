from pathlib import Path


def slice_text_by_position(text: str, pos: dict) -> str:
    """
    Replicate server-side slicing semantics (inclusive start, exclusive end).
    """
    start_line = max(1, pos.get("line_no"))
    start_col = max(0, pos.get("col_offset"))
    end_line = pos.get("end_line_no")
    end_col = pos.get("end_col_offset")

    collected: list[str] = []
    for idx, raw_line in enumerate(text.splitlines(True), start=1):
        if idx < start_line:
            continue

        line = raw_line[:-1] if raw_line.endswith("\n") else raw_line

        if end_line is None or idx < end_line:
            if idx == start_line:
                collected.append(line[start_col:])
            else:
                collected.append(line)
        elif idx == end_line:
            slice_end = None if end_col is None else end_col
            if idx == start_line:
                collected.append(line[start_col:slice_end])
            else:
                collected.append(line[:slice_end])
            break
        else:
            break

    return "\n".join(collected)


def find_child(node, name):
    """Find a child by name in a tree node dict."""
    for child in node.get("children", []):
        if child.get("name") == name:
            return child
    return None


def test_get_code_for_function(client, sample_project_path):
    # Create project from E2E sample
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "code_test_sample",
            "description": "code_test_sample",
            "path": sample_project_path,
        },
    )
    assert response.status_code == 200
    project_tree = response.json()

    # Navigate to core/utils/helper.py -> create_child
    project_tree["children"].sort(key=lambda x: x["name"])
    core_folder = find_child(project_tree, "core")
    assert core_folder is not None

    core_folder["children"].sort(key=lambda x: x["name"])
    utils_folder = find_child(core_folder, "utils")
    assert utils_folder is not None

    helper_py = find_child(utils_folder, "helper.py")
    assert helper_py is not None

    create_child_func = find_child(helper_py, "create_child")
    assert create_child_func is not None

    # Call get_code for function
    func_key = create_child_func["_key"]
    r_func = client.get(f"/api/v1/code-elements/{func_key}/code")
    assert r_func.status_code == 200
    payload = r_func.json()
    assert payload["node_type"] == "function"
    assert payload["name"] == "create_child"
    assert isinstance(payload.get("code"), str)
    assert "def create_child" in payload["code"]

    # Boundary check using returned position
    position = payload.get("position")
    assert isinstance(position, dict)
    # Read the file content to slice
    file_path = payload.get("file_path")
    # Resolve absolute path from our known sample project path
    source_abs = Path(sample_project_path) / file_path
    with open(source_abs, "r", encoding="utf-8") as f:
        source_text = f.read()
    expected_slice = slice_text_by_position(source_text, position)
    assert expected_slice == payload["code"]


def test_get_code_for_class(client, sample_project_path):
    # Create project from E2E sample
    response = client.post(
        "/api/v1/projects",
        json={
            "name": "code_test_sample",
            "description": "code_test_sample",
            "path": sample_project_path,
        },
    )
    assert response.status_code == 200
    project_tree = response.json()

    # Navigate to core/model/child.py -> class Child
    project_tree["children"].sort(key=lambda x: x["name"])
    core_folder = find_child(project_tree, "core")
    assert core_folder is not None

    model_folder = find_child(core_folder, "model")
    assert model_folder is not None

    child_py = find_child(model_folder, "child.py")
    assert child_py is not None

    child_class = find_child(child_py, "Child")
    assert child_class is not None

    class_key = child_class["_key"]
    r_class = client.get(f"/api/v1/code-elements/{class_key}/code")
    assert r_class.status_code == 200
    payload = r_class.json()
    assert payload["node_type"] == "class"
    assert payload["name"] == "Child"
    assert isinstance(payload.get("code"), str)
    assert "class Child" in payload["code"]

    # Boundary check using returned position
    position = payload.get("position")
    assert isinstance(position, dict)
    source_abs = Path(sample_project_path) / payload.get("file_path")
    with open(source_abs, "r", encoding="utf-8") as f:
        source_text = f.read()
    expected_slice = slice_text_by_position(source_text, position)
    assert expected_slice == payload["code"]


def test_get_code_for_nested_function(client):
    # Use unit sample: simple_function to verify nested function extraction
    from pathlib import Path

    simple_function_path = str(
        Path(__file__).resolve().parents[2]
        / "unit/parser/analyzer/function/simple_function"
    )

    response = client.post(
        "/api/v1/projects",
        json={
            "name": "code_test_nested",
            "description": "code_test_nested",
            "path": simple_function_path,
        },
    )
    assert response.status_code == 200
    project_tree = response.json()

    # Navigate to main.py -> factory -> add
    project_tree["children"].sort(key=lambda x: x["name"])
    main_py = find_child(project_tree, "main.py")
    assert main_py is not None

    factory_func = find_child(main_py, "factory")
    assert factory_func is not None

    add_func = find_child(factory_func, "add")
    assert add_func is not None

    nested_key = add_func["_key"]
    r_nested = client.get(f"/api/v1/code-elements/{nested_key}/code")
    assert r_nested.status_code == 200
    payload = r_nested.json()
    assert payload["node_type"] == "function"
    assert payload["name"] == "add"
    assert isinstance(payload.get("code"), str)
    assert "def add" in payload["code"]

    # Boundary check using returned position
    position = payload.get("position")
    assert isinstance(position, dict)
    source_abs = (
        Path(simple_function_path) / payload.get("file_path")
    )
    with open(source_abs, "r", encoding="utf-8") as f:
        source_text = f.read()
    expected_slice = slice_text_by_position(source_text, position)
    assert expected_slice == payload["code"]
