# Design Patterns for Async ArangoDB

## Overview

This document presents proven design patterns for building robust, performant async applications with ArangoDB. Each pattern includes motivation, implementation, and real examples from the codebase.

---

## Pattern 1: Async Repository Pattern

### Motivation
Encapsulate all database access logic in repository classes, providing a clean interface for services while handling async complexity internally.

### Structure

```python
from typing import List, Optional, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class AsyncBaseRepository(Generic[T]):
    """Base async repository with common CRUD operations."""
    
    def __init__(self, db: AsyncDatabase, collection_name: str, model: Type[T]):
        self.db = db
        self.collection_name = collection_name
        self.model = model
        self._collection = None
    
    async def _get_collection(self):
        """Lazy-load collection handle."""
        if self._collection is None:
            self._collection = await self.db.collection(self.collection_name)
        return self._collection
    
    async def get_by_key(self, key: str) -> Optional[T]:
        """Get document by key."""
        collection = await self._get_collection()
        doc = await collection.get(key)
        return self.model.model_validate(doc) if doc else None
    
    async def create(self, entity: T) -> T:
        """Create new document."""
        collection = await self._get_collection()
        dump = entity.model_dump(by_alias=True, exclude_none=True)
        meta = await collection.insert(dump, return_new=True)
        return self.model.model_validate(meta['new'])
    
    async def find(self, filters: dict, limit: Optional[int] = None) -> List[T]:
        """Find documents matching filters."""
        collection = await self._get_collection()
        cursor = await collection.find(filters, limit=limit)
        
        results = []
        async for doc in cursor:
            results.append(self.model.model_validate(doc))
        return results
    
    async def aql(self, query: str, bind_vars: dict = None) -> List[T]:
        """Execute AQL query and return typed results."""
        cursor = await self.db.aql.execute(query, bind_vars=bind_vars or {})
        
        results = []
        async for doc in cursor:
            results.append(self.model.model_validate(doc))
        return results
```

### Domain Repository Example

```python
class AsyncCallRepository(AsyncBaseRepository[CallNode]):
    def __init__(self, db: AsyncDatabase):
        super().__init__(db, "nodes", CallNode)
    
    async def find_by_target_and_parent(
        self,
        target_id: str,
        parent_id: str
    ) -> Optional[CallNode]:
        """Find call by target and parent (domain-specific query)."""
        query = """
        FOR c IN 1..1 OUTBOUND @parent_id contains_edges
            FILTER c.node_type == "call"
            LET t = FIRST(FOR target IN 1..1 OUTBOUND c targets_edges RETURN target)
            FILTER t != null && t._id == @target_id
            LIMIT 1
            RETURN c
        """
        
        cursor = await self.db.aql.execute(
            query,
            bind_vars={'parent_id': parent_id, 'target_id': target_id}
        )
        
        doc = await cursor.next() if cursor else None
        return CallNode.model_validate(doc) if doc else None
    
    async def find_batch_by_target_parent(
        self,
        pairs: List[Tuple[str, str]]
    ) -> Dict[Tuple[str, str], Optional[CallNode]]:
        """Batch version - find multiple calls in one query."""
        query = """
        FOR pair IN @pairs
            LET result = FIRST(
                FOR call IN 1..1 OUTBOUND pair.parent_id contains_edges
                    FILTER call.node_type == "call"
                    LET target = FIRST(FOR t IN 1..1 OUTBOUND call targets_edges RETURN t)
                    FILTER target != null && target._id == pair.target_id
                    RETURN {parent_id: pair.parent_id, target_id: pair.target_id, call: call}
            )
            RETURN result
        """
        
        cursor = await self.db.aql.execute(
            query,
            bind_vars={'pairs': [{'parent_id': p, 'target_id': t} for p, t in pairs]}
        )
        
        results = {}
        async for row in cursor:
            if row and 'call' in row:
                key = (row['parent_id'], row['target_id'])
                results[key] = CallNode.model_validate(row['call'])
        
        return results
```

---

## Pattern 2: Unit of Work (Transaction Management)

### Motivation
Group multiple repository operations into a single transaction, ensuring atomicity.

### Implementation

```python
class UnitOfWork:
    """Manages a transaction across multiple repositories."""
    
    def __init__(self, db: AsyncDatabase):
        self.db = db
        self._transaction = None
        self._committed = False
    
    async def __aenter__(self):
        """Start transaction."""
        self._transaction = await self.db.begin_transaction(
            write=['nodes', 'contains_edges', 'targets_edges']
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Commit or rollback transaction."""
        if exc_type is None and not self._committed:
            await self._transaction.commit()
        else:
            await self._transaction.abort()
    
    async def commit(self):
        """Explicitly commit transaction."""
        await self._transaction.commit()
        self._committed = True
    
    async def rollback(self):
        """Explicitly rollback transaction."""
        await self._transaction.abort()

# Usage
async def create_call_with_edges(call_node, parent_id, target_id):
    async with UnitOfWork(db) as uow:
        # All operations in one transaction
        call = await call_repo.create(call_node)
        await contains_repo.create(from_id=parent_id, to_id=call.id)
        await targets_repo.create(from_id=call.id, to_id=target_id)
        
        # Commit all or nothing
        await uow.commit()
```

---

## Pattern 3: Batch Processing with Concurrency Control

### Motivation
Process large datasets efficiently by batching and limiting concurrent operations.

### Implementation

```python
class BatchProcessor:
    """Process items in batches with controlled concurrency."""
    
    def __init__(self, batch_size: int = 100, max_concurrent: int = 10):
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch(self, items: List[T], processor: Callable) -> List[Any]:
        """Process a batch of items concurrently."""
        async def process_with_limit(item):
            async with self.semaphore:
                return await processor(item)
        
        tasks = [process_with_limit(item) for item in items]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def process_all(self, items: List[T], processor: Callable) -> List[Any]:
        """Process all items in batches."""
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = await self.process_batch(batch, processor)
            results.extend(batch_results)
            
            logger.info(f"Processed batch {i//self.batch_size + 1}, "
                       f"total items: {len(results)}")
        
        return results

# Usage
async def sync_all_calls(call_infos: List[CallInfo]):
    processor = BatchProcessor(batch_size=500, max_concurrent=20)
    
    async def sync_single_call(info):
        return await call_sync_service.sync_call(info)
    
    results = await processor.process_all(call_infos, sync_single_call)
    return results
```

---

## Pattern 4: Retry with Exponential Backoff

### Motivation
Handle transient failures (network blips, DB locks) gracefully.

### Implementation

```python
import asyncio
from typing import TypeVar, Callable

T = TypeVar('T')

async def retry_async(
    func: Callable[..., Awaitable[T]],
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    exceptions: Tuple = (Exception,)
) -> T:
    """Retry an async function with exponential backoff."""
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            
            if attempt < max_retries:
                logger.warning(
                    f"Attempt {attempt + 1} failed: {e}. "
                    f"Retrying in {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
                delay *= backoff_factor
            else:
                logger.error(f"All {max_retries + 1} attempts failed")
    
    raise last_exception

# Usage
async def fetch_with_retry(node_id):
    return await retry_async(
        lambda: node_repo.get_by_id(node_id),
        max_retries=3,
        exceptions=(ArangoServerError, ArangoNetworkError)
    )
```

---

## Pattern 5: Async Generator for Streaming

### Motivation
Process large result sets without loading everything into memory.

### Implementation

```python
class StreamingRepository:
    """Repository with streaming query methods."""
    
    async def stream_all(self, batch_size: int = 1000):
        """Stream all documents as async generator."""
        query = f"FOR doc IN {self.collection_name} RETURN doc"
        cursor = await self.db.aql.execute(query, batch_size=batch_size)
        
        async for doc in cursor:
            yield self.model.model_validate(doc)
    
    async def stream_filtered(self, filter_func, batch_size: int = 1000):
        """Stream documents matching a Python filter."""
        async for doc in self.stream_all(batch_size):
            if filter_func(doc):
                yield doc

# Usage
async def process_large_dataset():
    repo = StreamingRepository(db, "nodes", Node)
    
    async for node in repo.stream_filtered(lambda n: n.node_type == "function"):
        await process_node(node)
        # Only one node in memory at a time!
```

---

## Pattern 6: Dependency Injection with Async

### Motivation
Manage dependencies and lifecycle of async resources.

### Implementation

```python
from contextlib import asynccontextmanager

class ServiceLocator:
    """Dependency injection container for async services."""
    
    def __init__(self):
        self._services = {}
        self._clients = {}
    
    async def initialize(self):
        """Initialize all async resources."""
        # Create database client
        self._clients['arango'] = await create_arango_client()
        
        # Create repositories
        db = self._clients['arango']
        self._services['node_repo'] = AsyncNodeRepository(db)
        self._services['call_repo'] = AsyncCallRepository(db)
        
        # Create services
        self._services['container_service'] = ContainerService(
            self.get('node_repo'),
            self.get('call_repo')
        )
    
    def get(self, name: str):
        """Get a service by name."""
        return self._services[name]
    
    async def cleanup(self):
        """Clean up all async resources."""
        for client in self._clients.values():
            await client.close()

@asynccontextmanager
async def app_context():
    """Application context manager."""
    locator = ServiceLocator()
    await locator.initialize()
    try:
        yield locator
    finally:
        await locator.cleanup()

# Usage
async def main():
    async with app_context() as services:
        container_service = services.get('container_service')
        result = await container_service.do_something()
```

---

## Pattern 7: Event-Driven Architecture

### Motivation
Decouple components and enable reactive programming.

### Implementation

```python
from typing import Callable, List
from enum import Enum

class EventType(Enum):
    NODE_CREATED = "node_created"
    NODE_UPDATED = "node_updated"
    NODE_DELETED = "node_deleted"

class AsyncEventBus:
    """Simple async event bus."""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable]] = {}
    
    def subscribe(self, event_type: EventType, handler: Callable):
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    async def publish(self, event_type: EventType, data: Any):
        """Publish an event."""
        handlers = self._handlers.get(event_type, [])
        
        # Execute all handlers concurrently
        tasks = [handler(data) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

# Usage
event_bus = AsyncEventBus()

# Subscribe handlers
async def on_node_created(node):
    logger.info(f"Node created: {node.id}")
    await update_search_index(node)

event_bus.subscribe(EventType.NODE_CREATED, on_node_created)

# Publish events
async def create_node(node_data):
    node = await node_repo.create(node_data)
    await event_bus.publish(EventType.NODE_CREATED, node)
    return node
```

---

## Pattern 8: Circuit Breaker

### Motivation
Prevent cascading failures by detecting unhealthy services.

### Implementation

```python
from enum import Enum
import time

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """Circuit breaker for async operations."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        recovery_timeout: float = 30.0
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        
        self.state = CircuitState.CLOSED
        self.fail_count = 0
        self.last_fail_time = None
    
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function through circuit breaker."""
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_fail_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            
            # Success - reset or close circuit
            if self.state == CircuitState.HALF_OPEN:
                logger.info("Circuit breaker: Service recovered")
                self.state = CircuitState.CLOSED
                self.fail_count = 0
            
            return result
        
        except Exception as e:
            self.fail_count += 1
            self.last_fail_time = time.time()
            
            if self.fail_count >= self.failure_threshold:
                logger.error("Circuit breaker: OPENED due to failures")
                self.state = CircuitState.OPEN
            
            raise

# Usage
db_circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

async def query_with_circuit(query):
    return await db_circuit.call(db.aql.execute, query)
```

---

## Complete Example: Async Sync Service

Putting it all together:

```python
class AsyncCallSyncService:
    """Fully async call synchronization service."""
    
    def __init__(
        self,
        call_repo: AsyncCallRepository,
        scope_manager: ScopeManager,
        event_bus: AsyncEventBus
    ):
        self.call_repo = call_repo
        self.scope_manager = scope_manager
        self.event_bus = event_bus
        self.batch_processor = BatchProcessor(batch_size=500, max_concurrent=20)
    
    async def sync_call_chains(self, root_scope_id: str):
        """Sync all call chains from root scope."""
        # 1. Collect all call infos (in-memory, fast)
        call_infos = []
        scopes = self.scope_manager.get_all_scopes()
        for scope in scopes:
            call_sites = scope_manager.get_call_sites(scope.id)
            call_infos.extend(call_sites)
        
        logger.info(f"Syncing {len(call_infos)} calls")
        
        # 2. Process in batches with concurrency control
        results = await self.batch_processor.process_all(
            call_infos,
            self._sync_single_call
        )
        
        # 3. Handle results
        successes = [r for r in results if not isinstance(r, Exception)]
        failures = [r for r in results if isinstance(r, Exception)]
        
        logger.info(f"Synced {len(successes)} calls, {len(failures)} failures")
        
        return successes
    
    async def _sync_single_call(self, call_info):
        """Sync a single call with retry."""
        return await retry_async(
            lambda: self._sync_call_impl(call_info),
            max_retries=3
        )
    
    async def _sync_call_impl(self, call_info):
        """Implementation of call sync."""
        # Check if call already exists
        existing = await self.call_repo.find_by_target_and_parent(
            call_info.target_id,
            call_info.parent_id
        )
        
        if existing:
            return existing  # Already synced
        
        # Create new call node
        call_node = CallNode(
            name=call_info.name,
            # ... other fields
        )
        
        async with UnitOfWork(self.call_repo.db) as uow:
            # Create node and edges in one transaction
            created_call = await self.call_repo.create(call_node)
            await self._create_edges(created_call, call_info)
            await uow.commit()
        
        # Publish event
        await self.event_bus.publish(EventType.NODE_CREATED, created_call)
        
        return created_call
```

---

## Summary

These patterns provide:
- ✅ Clean separation of concerns
- ✅ Proper async resource management
- ✅ Controlled concurrency
- ✅ Error resilience
- ✅ Streaming for large datasets
- ✅ Event-driven architecture
- ✅ Testability

Use these as templates for your migration!
