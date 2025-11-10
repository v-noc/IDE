from contextlib import AsyncExitStack

from starlette.types import ASGIApp, Receive, Scope, Send


# Used mainly to close files after the request is done, dependencies are closed
# in their own AsyncExitStack
class AsyncExitStackMiddleware:
    """ID: cdb150bc-6555-4beb-8e34-8cf26eab6451"""
    def __init__(
        self, app: ASGIApp, context_name: str = "fastapi_middleware_astack"
    ) -> None:
        """ID: d3610642-c6a5-4fd4-a037-b8b845a0e45e"""
        self.app = app
        self.context_name = context_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ID: a85741e0-e622-40c7-a778-8bc4ce9f2e69"""
        async with AsyncExitStack() as stack:
            scope[self.context_name] = stack
            await self.app(scope, receive, send)
