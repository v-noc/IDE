# vn-logger

`vn-logger` is a Python logging package that provides a decorator for context-aware logging and sends log data to a JSON-RPC endpoint.

## Installation

This package is intended to be used as a workspace package within the `v-noc` project. Ensure it's included in your `pyproject.toml` like this:

```toml
[tool.uv.sources]
vn-logger = { workspace = true }
```

And as a dependency:
```toml
[project]
dependencies = [
    "vn-logger"
]
```

## Usage

### 1. Configure the Logger

First, you need to configure the logger with your JSON-RPC endpoint and a project ID. This should be done once when your application starts.

```python
from vn_logger import configure_logger

configure_logger("http://localhost:8000/jsonrpc", "your-project-id")
```

### 2. Use the `context_logger` Decorator

Apply the `context_logger` decorator to any function you want to monitor. You must provide a unique `function_id` for each decorated function.

```python
from vn_logger import context_logger

@context_logger(function_id="some-unique-function-id")
def my_function(arg1, arg2):
    # Your function logic here
    return "result"

my_function("a", "b")
```

The logger will automatically capture:
- Function entry and exit.
- Arguments and return values.
- Execution duration.
- Unhandled exceptions.
- A `chain_id` to trace a sequence of calls.
- The `parent_function_id` to build a call hierarchy.
