def test_create_project(client, sample_project_path):
    response = client.post("/api/v1/projects", json={
        "name": "test_project",
        "description": "test_project",
        "path": sample_project_path
    })
    print(response.json())
    # assert response.status_code == 200
    # assert response.json() == {"name": "test_project",
    #                            "description": "test_project", "path": "test_project"}
