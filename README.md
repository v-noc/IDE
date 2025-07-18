# V-NOC Monorepo

This project is a monorepo containing a frontend and a backend application.

## Prerequisites

- [Node.js and Yarn](https://yarnpkg.com/getting-started/install)
- [Python and uv](https://github.com/astral-sh/uv)
- [ArangoDB](https://www.arangodb.com/download-major/)

## Setup

1.  **Install all dependencies:**

    ```bash
    make install
    ```

## Running the Application

To run the application for development, you'll need to run the backend and frontend servers in separate terminals.

1.  **Run the backend server:**

    ```bash
    make run-backend
    ```

    The backend will be available at `http://localhost:8000`.

2.  **Run the frontend server:**

    ```bash
    make run-frontend
    ```

    The frontend will be available at `http://localhost:5173`.

## ArangoDB

The backend uses ArangoDB as its database. Make sure you have an ArangoDB instance running and accessible at `http://localhost:8529` with the default username (`root`) and no password.

The application will automatically create a `users` collection when you first create a user.
