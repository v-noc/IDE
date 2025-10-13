from fastapi_jsonrpc import BaseError


class CodeElementNotFoundError(BaseError):
    code = -32001
    message = "Code element not found"
    data = None


class ProjectNotFoundError(BaseError):
    code = -32002
    message = "Project not found"
    data = None
