# Async ArangoDB Setup with FastAPI

## The Challenge

The async ArangoDB client requires an `async with` context manager, but FastAPI's dependency injection system and your application lifecycle need careful integration. This document explains the complete setup.

---

## Current Sync Pattern (What You Have)

```python
# client.py (sync - current)
_client: ArangoClient | None = None
_db_connection: StandardDatabase | None = None

def get_db() -> StandardDatabase:
    global _client, _db_connection
    if _client is None:
        _client = ArangoClient(hosts=settings.ARANGO_HOST)
    
    if _db_connection is None:
        _db_connection = _client.db(
            settings.ARANGO_DB,
            username=settings.ARANGO_USER,
            password=settings.ARANGO_PASSWORD
        )
    return _db_connection

# main.py (sync - current)
@asynccontextmanager
async def lifespan(app: FastAPI):
    db = get_db()  # Direct call, no await
    yield
    # No cleanup needed

# dependencies.py (sync - current)  
def get_project_service(db: StandardDatabase = Depends(get_db)):
    repos = Repositories(db)
    return ProjectService(repos)
```

---

## Async Pattern (What You Need)

### Option 1: Lifespan Management (Recommended)

**Pattern**: Create the async client/database in the FastAPI lifespan, store in `app.state`, inject via dependencies.

#### Step 1: Update `client.py`

```python
# src/backend/app/db/client.py
from contextlib import asynccontextmanager
from arangoasync import ArangoClient
from arangoasync.auth import Auth
from arangoasync.database import AsyncDatabase
from ..config.settings import get_settings

# Type hints for clarity
_client: ArangoClient | None = None
_db: AsyncDatabase | None = None
_http_session = None  # Will hold aiohttp.ClientSession


@asynccontextmanager
async def get_arango_client():
    """
    Create and manage the async ArangoDB client lifecycle.
    Use this in FastAPI's lifespan context.
    """
    import aiohttp
    
    settings = get_settings()
    
    # Create HTTP session with connection pooling
    connector = aiohttp.TCPConnector(
        limit=100,          # Max 100 connections total
        limit_per_host=50,  # Max 50 per ArangoDB instance
    )
    http_session = aiohttp.ClientSession(connector=connector)
    
    # Create ArangoDB client with custom session
    async with ArangoClient(
        hosts=settings.ARANGO_HOST,
        http_client=http_session
    ) as client:
        # Connect to database
        auth = Auth(
            username=settings.ARANGO_USER,
            password=settings.ARANGO_PASSWORD
        )
        db = await client.db(settings.ARANGO_DB, auth=auth)
        
        # Verify connection
        try:
            await db.properties()  # Test the connection
            print(f"✅ Connected to ArangoDB: {settings.ARANGO_DB}")
        except Exception as e:
            print(f"❌ Failed to connect to ArangoDB: {e}")
            raise
        
        yield db  # Provide database to the app
        
        # Cleanup happens automatically via context manager
        print("🔄 Closing ArangoDB connection...")
    
    # Close HTTP session
    await http_session.close()


# Dependency function for FastAPI
async def get_db_dependency() -> AsyncDatabase:
    """
    FastAPI dependency to get database from app.state.
    
    Usage in route:
        async def my_route(db: AsyncDatabase = Depends(get_db_dependency)):
            ...
    """
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    
    # This will be set by the middleware or dependency
    # For now, we'll use a workaround via FastAPI's Request object
    # See the dependencies.py update below for the full pattern
    raise NotImplementedError("Use get_db() via app.state instead")
```

#### Step 2: Update `main.py`

```python
# src/backend/app/main.py
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .db.client import get_arango_client
from .core.watcher.service import WatcherService
from .api import root


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for the application's lifespan.
    Handles startup and shutdown events.
    """
    # Startup: Initialize async database
    async with get_arango_client() as db:
        # Store database in app state for dependency injection
        app.state.db = db
        print("✅ Database connection established and stored in app.state")
        
        # Initialize watcher service (if needed)
        watcher_service = WatcherService()
        watcher_service.set_db(db)
        watcher_service.set_event_loop(asyncio.get_running_loop())
        app.state.watcher_service = watcher_service
        
        print("🔌 Application startup complete")
        
        yield  # App runs here
        
        # Shutdown: Cleanup
        print("🔄 Shutting down...")
        try:
            if hasattr(app.state, "watcher_service"):
                app.state.watcher_service.stop_all()
        except Exception as e:
            print(f"⚠️ Watcher cleanup failed: {e}")
        
        # Database connection cleanup happens via context manager
        print("✅ Shutdown complete")


app = FastAPI(
    title="V-NOC API",
    version="1.0.0",
    lifespan=lifespan,  # Connect the lifespan
)

# ... rest of your app setup
```

#### Step 3: Update `dependencies.py`

```python
# src/backend/app/api/dependencies.py
from fastapi import Depends, Request
from arangoasync.database import AsyncDatabase

from app.core.repository import Repositories
from app.core.services.project_service import ProjectService
from app.core.services.container_service import ContainerService
# ... other imports


# Database dependency
async def get_db(request: Request) -> AsyncDatabase:
    """
    Get database from app state.
    
    The database is initialized in the lifespan context and stored
    in app.state.db. This dependency retrieves it.
    """
    return request.app.state.db


# Service dependencies (now async)
async def get_project_service(
    db: AsyncDatabase = Depends(get_db),
) -> ProjectService:
    repos = Repositories(db)
    return ProjectService(repos)


async def get_container_service(
    db: AsyncDatabase = Depends(get_db),
) -> ContainerService:
    repos = Repositories(db)
    return ContainerService(repos)


# ... rest of services (make them all async)
async def get_file_service(db: AsyncDatabase = Depends(get_db)):
    return FileService(Repositories(db))

async def get_class_service(db: AsyncDatabase = Depends(get_db)):
    return ClassService(Repositories(db))

async def get_function_service(db: AsyncDatabase = Depends(get_db)):
    return FunctionService(Repositories(db))

async def get_call_service(db: AsyncDatabase = Depends(get_db)):
    return CallService(Repositories(db))

async def get_log_service(db: AsyncDatabase = Depends(get_db)):
    return LogService(Repositories(db))

async def get_group_service(db: AsyncDatabase = Depends(get_db)):
    return GroupService(Repositories(db))
```

#### Step 4: Update Your Routes

**Before (sync)**:
```python
@router.get("/projects/{project_id}")
def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
):
    return service.get_project(project_id)
```

**After (async)**:
```python
@router.get("/projects/{project_id}")
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
):
    return await service.get_project(project_id)  # Add await!
```

---

## Option 2: Lazy Initialization (Alternative)

If you prefer the old pattern but with async:

```python
# client.py (alternative approach)
from contextlib import asynccontextmanager
import asyncio

_client = None
_db = None
_lock = asyncio.Lock()


async def get_db() -> AsyncDatabase:
    """Get or create async database connection (lazy)."""
    global _client, _db
    
    async with _lock:  # Ensure thread-safety
        if _db is None:
            settings = get_settings()
            
            # Create client
            _client = ArangoClient(hosts=settings.ARANGO_HOST)
            
            # Create database
            auth = Auth(username=settings.ARANGO_USER, password=settings.ARANGO_PASSWORD)
            _db = await _client.db(settings.ARANGO_DB, auth=auth)
            
            print("✅ Database initialized")
        
        return _db


async def close_db():
    """Close database connection."""
    global _client, _db
    
    if _client:
        await _client.close()
        _client = None
        _db = None


# In main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB
    db = await get_db()
    app.state.db = db
    
    yield
    
    # Shutdown: Close DB
    await close_db()
```

**⚠️ Warning**: This approach is less clean because:
- The `async with` pattern is recommended by the library
- Connection pooling setup is less obvious
- Cleanup is manual

---

## Recommended Structure

```
src/backend/app/
├── db/
│   ├── __init__.py
│   └── client.py          # Async client setup
├── core/
│   ├── repository/
│   │   ├── base/
│   │   │   └── base_collection.py   # Make async
│   │   └── ...
│   └── services/
│       └── ...                       # Make async
├── api/
│   ├── dependencies.py    # Async dependencies
│   └── routes/
│       └── ...            # Async routes
└── main.py               # Lifespan with async DB
```

---

## Step-by-Step Migration Checklist

### Phase 1: Database Layer
- [ ] Update `client.py` with `get_arango_client()` context manager
- [ ] Update `main.py` lifespan to use `async with get_arango_client()`
- [ ] Store `db` in `app.state.db`
- [ ] Test: `uvicorn app.main:app` should show "✅ Connected to ArangoDB"

### Phase 2: Dependencies
- [ ] Update `get_db()` in `dependencies.py` to read from `request.app.state.db`
- [ ] Make all `get_*_service()` functions async
- [ ] Change `StandardDatabase` to `AsyncDatabase` in type hints
- [ ] Test: Import dependencies module (no errors)

### Phase 3: Repositories
- [ ] Convert `BaseRepository` methods to async (add `async def`, `await`)
- [ ] Update all repository method calls to use `await`
- [ ] Test: Run simple repository query

### Phase 4: Services
- [ ] Convert service methods to async
- [ ] Update all DB calls to use `await`
- [ ] Test: Call a service method

### Phase 5: Routes
- [ ] Convert route handlers to `async def`
- [ ] Add `await` to all service calls
- [ ] Test: Make API request, verify response

---

## Common Issues & Solutions

### Issue 1: "RuntimeError: no running event loop"

**Cause**: Trying to call async code from sync context

**Solution**: Make the calling function async
```python
# ❌ Bad
def my_route(service = Depends(get_service)):
    result = service.get_data()  # service.get_data is async!

# ✅ Good
async def my_route(service = Depends(get_service)):
    result = await service.get_data()
```

### Issue 2: "coroutine was never awaited"

**Cause**: Forgot `await` keyword

**Solution**: Add `await`
```python
# ❌ Bad
data = db.collection.find({})

# ✅ Good
data = await db.collection.find({})
```

### Issue 3: "AsyncDatabase object has no attribute 'properties'"

**Cause**: Method names might differ between sync and async versions

**Solution**: Check the async API docs or use `dir(db)` to see available methods

### Issue 4: Can't access `app.state.db` in dependency

**Cause**: Need `Request` object to access app state

**Solution**:
```python
from fastapi import Request

async def get_db(request: Request):
    return request.app.state.db
```

---

## Testing Your Setup

### Quick Test Script

```python
# test_db_connection.py
import asyncio
from app.db.client import get_arango_client

async def test():
    async with get_arango_client() as db:
        print(f"Database: {db.name}")
        
        # Test query
        cursor = await db.aql.execute("RETURN 1 + 1")
        result = await cursor.next()
        print(f"Test query result: {result}")  # Should be 2
        
        print("✅ Connection test passed!")

if __name__ == "__main__":
    asyncio.run(test())
```

Run: `python -m app.test_db_connection`

---

## Summary

**Recommended Approach**: Option 1 (Lifespan Management)

1. **Create async client in lifespan**: Use `async with get_arango_client()` 
2. **Store in app.state**: `app.state.db = db`
3. **Inject via dependency**: `async def get_db(request: Request)`
4. **Use in routes**: `async def route(..., db = Depends(get_db))`

This pattern:
- ✅ Properly manages connection lifecycle
- ✅ Enables connection pooling
- ✅ Integrates cleanly with FastAPI
- ✅ Follows async best practices
- ✅ Ensures cleanup on shutdown

The key insight is that the `async with` context is managed by FastAPI's lifespan, not by individual requests or dependencies.
