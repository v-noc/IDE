# V-NOC Monorepo

This project is a monorepo containing a frontend and a backend application.

## Prerequisites

- [Node.js and Yarn](https://yarnpkg.com/getting-started/install)
- [Python and uv](https://github.com/astral-sh/uv)
- [Docker and Docker Compose](https://docs.docker.com/get-docker/)

## Setup

1.  **Install all dependencies:**

    ```bash
    make install
    ```

## Running the Application

To run the application for development, you'll need to run the backend and frontend servers in separate terminals.

1.  **Start the ArangoDB database:**

    ```bash
    make start-db
    ```

2.  **Run the backend server:**

    ```bash
    make run-backend
    ```

    The backend will be available at `http://localhost:8000`.

3.  **Run the frontend server:**

    ```bash
    make run-frontend
    ```

    The frontend will be available at `http://localhost:5173`.

## API Documentation

The API documentation is automatically generated using FastAPI's OpenAPI integration. Once the backend server is running, you can access the documentation at the following URLs:

-   **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
-   **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
