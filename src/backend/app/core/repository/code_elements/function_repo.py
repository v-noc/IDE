from app.db.async_terminus_client import AsyncClient


class FunctionRepo():
    def __init__(self, client: AsyncClient):
        self.client = client

    def get_function_by_id(self, function_id: str):
        pass

    def get_function_by_filed(self, field_name: str, field_value: str):
        pass

    def get_children(self, function_id: str, child_type: str):
        pass
