# Driver Protocol: JSON-RPC 2.0 over HTTP

## Why JSON-RPC

- **Single endpoint** (`POST /rpc`) — no REST route sprawl
- **Batch support** — send multiple parse requests in one HTTP call
- **Standardized** error codes, request/response format
- **Language-agnostic** — trivial to implement in Python, JS/TS, Go, etc.
- **Same protocol as LSP** — familiar to anyone who's built language tooling

## Driver Lifecycle

```
Backend                          Python Driver
   │                                  │
   │──── start process ──────────────►│  (subprocess or docker)
   │                                  │
   │◄─── listening on port ──────────│  (stdout: "READY port=9100")
   │                                  │
   │──── initialize ─────────────────►│  (project path, env config)
   │◄─── ok ─────────────────────────│
   │                                  │
   │──── parse_file ─────────────────►│  (many times)
   │◄─── nodes + content ────────────│
   │                                  │
   │──── resolve_mro ────────────────►│
   │◄─── base_classes ───────────────│
   │                                  │
   │──── resolve_calls ──────────────►│
   │◄─── call_frame_stack ───────────│
   │                                  │
   │──── shutdown ───────────────────►│
   │                                  X
```

The backend starts the driver as a **subprocess** (or connects to a running container).
The driver prints `READY port=<PORT>` to stdout. The backend reads this, stores the port,
and begins sending JSON-RPC requests.

## Transport

- **HTTP POST** to `http://localhost:<PORT>/rpc`
- **Content-Type**: `application/json`
- **JSON-RPC 2.0** envelope for every request/response

## Shared Types

These are the wire types used in request/response payloads. They mirror the existing
Pydantic models in `parser/ast/models.py`.

```jsonc
// NodePosition
{
  "line": 10,
  "column": 0,
  "end_line": 25,
  "end_column": 4
}

// Symbol (corresponds to BaseNode / FunctionNode / ClassNode / CallNode)
{
  "id": "FunctionSchema/abc-123",     // stable ID (injected by driver)
  "name": "my_function",
  "type": "function",                  // "class" | "function" | "call"
  "position": { ... },                 // NodePosition
  "children": [ ... ],                 // nested Symbols
  // call-specific (only when type == "call"):
  "call_index": 0,
  "call_col_pos": 5,
  // class-specific (only when type == "class", returned by parse_file):
  "base_classes": ["module.BaseClass", "builtins.object"]
}

// CallFrame (corresponds to CallFrameStack)
{
  "target_qname": "module.submodule.function_name",
  "target_id": "FunctionSchema/abc-123",
  "children": [ ... ]                  // nested CallFrames
}
```

---

## Methods

### 1. `initialize`

Called once after driver starts. Configures the language environment for a project.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "project_path": "/absolute/path/to/project",
    "language": "python",
    "config": {}
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "status": "ok",
    "extensions": [".py"]
  }
}
```

---

### 2. `parse_file`

Inject stable IDs (if missing) and parse the file into a symbol tree.
This replaces the current `scan()` function.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "parse_file",
  "params": {
    "file_path": "/absolute/path/to/file.py",
    "content": "class Foo:\n    \"\"\"ID: abc-123\"\"\"\n    def bar(self): ...",
    "resolve_mro": true
  }
}
```

`resolve_mro`: When `true`, the driver resolves MRO for all class nodes in the file
and includes `base_classes` on each class symbol. This avoids a separate `resolve_mro`
call per class (fewer round trips).

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "nodes": [
      {
        "id": "ClassSchema/abc-123",
        "name": "Foo",
        "type": "class",
        "position": { "line": 1, "column": 0, "end_line": 3, "end_column": 35 },
        "base_classes": ["module.Foo", "builtins.object"],
        "children": [
          {
            "id": "FunctionSchema/def-456",
            "name": "bar",
            "type": "function",
            "position": { "line": 3, "column": 4, "end_line": 3, "end_column": 35 },
            "children": []
          }
        ]
      }
    ],
    "content": "class Foo:\n    \"\"\"ID: abc-123\"\"\"\n    def bar(self):\n        \"\"\"ID: def-456\"\"\"\n        ...",
    "modified": true
  }
}
```

- `nodes`: The parsed symbol tree (same shape as current `List[BaseNode]`)
- `content`: Source with IDs injected (same as current `processed_content`)
- `modified`: Whether the source was changed (IDs were injected)

---

### 3. `resolve_calls`

Resolve call hierarchy for a set of call sites within a scope.
This replaces `CallHierarchyResolver.resolve_call_hierarchy()`.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "resolve_calls",
  "params": {
    "file_path": "/absolute/path/to/file.py",
    "calls": [
      {
        "name": "some_function",
        "type": "call",
        "position": { "line": 15, "column": 4, "end_line": 15, "end_column": 20 },
        "call_index": 0,
        "call_col_pos": 4
      }
    ]
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "call_frame_stack": {
      "target_qname": "root",
      "target_id": "root",
      "children": [
        {
          "target_qname": "module.some_function",
          "target_id": "FunctionSchema/ghi-789",
          "children": []
        }
      ]
    }
  }
}
```

---

### 4. `read_or_inject_file_id`

Read or inject a stable FileID for a source file. This replaces `FileTracker.process_file()`.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "read_or_inject_file_id",
  "params": {
    "file_path": "/absolute/path/to/file.py"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "file_id": "FileSchema/abc-123",
    "modified": false
  }
}
```

If the file didn't have a FileID, the driver generates one, injects it (Python: into module
docstring), writes the file, and returns `"modified": true`.

---

### 5. `read_or_inject_folder_id`

Same as above but for folders. Python driver handles `__init__.py` + FolderID injection.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "read_or_inject_folder_id",
  "params": {
    "folder_path": "/absolute/path/to/package"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "folder_id": "FolderSchema/xyz-789",
    "modified": false
  }
}
```

---

### 6. `shutdown`

Graceful shutdown. The driver cleans up resources and exits.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "shutdown"
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "result": { "status": "ok" }
}
```

---

## Error Handling

Standard JSON-RPC 2.0 error codes:

| Code | Meaning | When |
|------|---------|------|
| -32700 | Parse error | Malformed JSON |
| -32600 | Invalid request | Missing method/params |
| -32601 | Method not found | Unknown method name |
| -32602 | Invalid params | Bad parameter types |
| -32603 | Internal error | Driver-side exception |
| -32000 | Not initialized | Method called before `initialize` |

Example error response:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "error": {
    "code": -32603,
    "message": "Failed to parse file",
    "data": { "file_path": "/path/to/file.py", "detail": "SyntaxError at line 42" }
  }
}
```

For non-fatal parse errors (e.g., MRO resolution fails for one class), the driver should
still return a successful response with partial data (empty `base_classes`) rather than
an error. This matches the current behavior where exceptions are caught and logged.

---

## Batch Requests

JSON-RPC 2.0 supports batch requests natively. Useful for parsing multiple files:

```json
[
  { "jsonrpc": "2.0", "id": 1, "method": "parse_file", "params": { "file_path": "a.py", "content": "...", "resolve_mro": true } },
  { "jsonrpc": "2.0", "id": 2, "method": "parse_file", "params": { "file_path": "b.py", "content": "...", "resolve_mro": true } }
]
```

Responses come back as an array in the same order. This reduces HTTP overhead when
processing many files during a resync.

---

## Design Decisions

### Why HTTP instead of stdio?

- Easier to test independently (curl, Postman, httpie)
- Can run driver standalone for debugging
- Natural fit for batch requests
- Familiar tooling

### Why stateful (initialize → use → shutdown)?

- Jedi project setup is expensive — do it once
- Driver can maintain internal caches (inference state, parsed modules)
- Matches the current `JediProjectManager` lifecycle

### Why `resolve_mro` inside `parse_file`?

- MRO resolution needs the same Jedi project context as parsing
- Doing it in one call avoids a round-trip per class
- `resolve_mro: true` flag makes it opt-in (Phase 1 collection needs it, Phase 2 doesn't)
- Keeps `ASTProcessor._resolve_mro` from needing its own driver call

### Why separate `resolve_calls` method?

- Call resolution happens in Phase 2 (analysis), separate from Phase 1 (collection)
- Call resolution is per-scope, not per-file — different granularity than `parse_file`
- Call resolution is expensive and benefits from being parallelized separately
