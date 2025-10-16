import fastapi_jsonrpc as jsonrpc

from .entrypoint import api_v1_logs


app = jsonrpc.API()
app.bind_entrypoint(api_v1_logs)
