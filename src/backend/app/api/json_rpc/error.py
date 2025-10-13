from fastapi_jsonrpc import BaseError


class ProjectNotFoundError(BaseError):
    CODE = -32000
    MESSAGE = "Project not found"


class CodeElementNotFoundError(BaseError):
    CODE = -32001
    MESSAGE = "Code element not found"


class FunctionNotFoundError(BaseError):
    CODE = -32002
    MESSAGE = "Function not found"
