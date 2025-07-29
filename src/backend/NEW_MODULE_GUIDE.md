# How to Add a New API Module

This guide provides a step-by-step process for adding a new API module to the backend, ensuring it integrates correctly with the existing structure, including routing, dependency management, and error handling.

## 1. Create the CRUD File

Your CRUD (Create, Read, Update, Delete) logic will be the core of your new module.

1.  **Create a New File:**
    *   Navigate to `src/backend/app/api/core/`.
    *   Create a new folder for your module (e.g., `my_new_module`).
    *   Inside, create a `crud.py` file.

2.  **Define Your Router:**
    *   In `crud.py`, create an `APIRouter` instance:
        ```python
        from fastapi import APIRouter
        
        router = APIRouter()
        ```

3.  **Implement Your Endpoints:**
    *   Define your Pydantic models for request and response bodies.
    *   Write your endpoint functions, using FastAPI decorators (`@router.get`, `@router.post`, etc.).
    *   Use `Depends` for dependency injection (e.g., `CodeGraphManager`).
    *   Raise `HTTPException` for specific errors (e.g., 404 Not Found).

    **Example `crud.py`:**
    ```python
    from fastapi import APIRouter, Depends, HTTPException
    from pydantic import BaseModel
    
    # 1. Define models
    class Item(BaseModel):
        name: str
        description: str | None = None

    # 2. Create router
    router = APIRouter()

    # 3. Define endpoints
    @router.post("/items/", response_model=Item)
    def create_item(item: Item):
        if not item.name:
            raise HTTPException(status_code=400, detail="Name cannot be empty")
        # In a real app, you would save the item to the database here.
        return item
    ```

## 2. Integrate the New Module into the Main App

Once your CRUD file is ready, you need to tell the main FastAPI application to use it.

1.  **Edit `src/backend/app/main.py`:**
    *   Import your new CRUD module.
    *   Use `app.include_router()` to add your new router to the application.

    **Example `main.py` modification:**
    ```python
    # ... other imports
    from .api.core.my_new_module import crud as my_new_module_crud

    # ... app initialization

    # Include routers
    app.include_router(root.router)
    app.include_router(health.router, tags=["health"])
    app.include_router(projects_crud.router, prefix="/api/core", tags=["projects"])
    
    # Add your new router
    app.include_router(
        my_new_module_crud.router, 
        prefix="/api/core/my_new_module",  # Set a URL prefix for your module
        tags=["My New Module"]             # Add a tag for the OpenAPI docs
    )
    ```

## 3. Add Tests

Always add tests for your new endpoints.

1.  **Create a Test File:**
    *   Navigate to `src/backend/tests/e2e/core/`.
    *   Create a new folder for your module (e.g., `my_new_module`).
    *   Inside, create a `test_my_new_module_crud.py` file.

2.  **Write Your Tests:**
    *   Use FastAPI's `TestClient` to make requests to your new endpoints.
    *   Use `pytest` for structuring your tests.
    *   Test both success cases and expected errors (e.g., 404s, 400s).

    **Example Test:**
    ```python
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    def test_create_item():
        response = client.post(
            "/api/core/my_new_module/items/",
            json={"name": "Test Item", "description": "A test item"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Item"
    ```

By following these steps, you can ensure that new modules are added in a consistent, maintainable, and well-tested manner.
