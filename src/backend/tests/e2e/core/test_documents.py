from httpx import AsyncClient
import pytest


@pytest.mark.asyncio
async def test_document_crud_endpoints(client: AsyncClient, sample_project_node):
    project_id = sample_project_node.id

    # Create document
    create_resp = await client.post(
        f"/api/v1/documents/?project_id={project_id}",
        json={
            "name": "Doc1",
            "description": "Desc",
            "node_id": project_id,
        },
    )
    assert create_resp.status_code == 201
    document = create_resp.json()
    document_key = document["id"]

    # List documents for node
    list_resp = await client.get(f"/api/v1/documents/?node_id={project_id}&project_id={project_id}")
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert isinstance(docs, list) and len(docs) == 1
    assert docs[0]["id"] == document_key

    # Update document
    update_resp = await client.put(
        f"/api/v1/documents/?document_id={document_key}&project_id={project_id}",
        json={
            "node_id": project_id,
            "name": "Doc1-upd",
            "description": "Desc2",
            "data": "payload",
        },
    )

    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["name"] == "Doc1-upd"
    assert updated["description"] == "Desc2"
    assert updated["data"] == "payload"

    # Delete document
    del_resp = await client.delete(
        f"/api/v1/documents/?document_id={document_key}&node_id={project_id}&project_id={project_id}",
    )
    assert del_resp.status_code == 204

    # Verify list is empty
    list_resp_2 = await client.get(f"/api/v1/documents/?node_id={project_id}&project_id={project_id}")

    assert list_resp_2.status_code == 200
    assert list_resp_2.json() == []
