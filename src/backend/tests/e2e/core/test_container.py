import pytest


@pytest.mark.asyncio
async def test_update_theme(client, sample_project_node):
    response = await client.put(f"/api/v1/containers/{sample_project_node.key}/update-theme", json={
        "navbarColor": "dark"
    })
    assert response.status_code == 200
    container_node = response.json()
    assert container_node['theme_config']['navbarColor'] == "dark"


@pytest.mark.asyncio
async def test_update_basic_info(client, sample_project_node):
    response = await client.put(
        f"/api/v1/containers/{sample_project_node.key}/update-basic-info",
        json={
            "name": "New Project Name",
            "description": "New description.",
            "icon": "new-icon.png"
        }
    )
    assert response.status_code == 200
    container_node = response.json()
    assert container_node['name'] == "New Project Name"
    assert container_node['description'] == "New description."
    assert container_node['icon'] == "new-icon.png"
