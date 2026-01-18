# Step 1: Backend Support for Function ID

## Goal
Update the backend to store and return `function_id` with log nodes. This is a prerequisite for the frontend to link logs to code.

## Changes

### 1. Update Data Models
**File:** `src/backend/app/core/model/logs.py`
- Add `function_id: Optional[str]` field to `LogNode` class.

**File:** `src/backend/app/core/schemas/log_tree.py`
- Add `function_id: Optional[str]` field to `LogTreeNode` class.

### 2. Update Log Service
**File:** `src/backend/app/core/services/log_service.py`
- In `create` method:
    - Pass `function_id` when initializing `LogNode`.
- In `create_batch` method:
    - Include `function_id` when creating `LogNode` instances.
    - Note: `function_id` is already present in `p.function_id` in the batch loop (`func_edges` creation uses it).

### 3. Verification
- Create a test log entry.
- Verify `function_id` is stored in the database document.
- distinct `function_id` field in `LogTreeNode` response.
