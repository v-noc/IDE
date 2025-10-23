
## Quick Start (Setup & Install)

### Prerequisites
- **Python** 3.11+ and **uv**
- **Node.js** 18+ and **Yarn**
- **Docker** and **Docker Compose** (for the database)

### 1) Create Python virtual environment
```bash
uv venv .venv
```

### 2) Install dependencies
- **All (backend + frontend)**
```bash
make install
```

- **Backend only**
```bash
make install-backend
```

- **Frontend only**
```bash
make install-frontend
```

### Optional: Database container
```bash
make start-db   # start ArangoDB
make stop-db    # stop ArangoDB
```

See the `Makefile` for additional commands.