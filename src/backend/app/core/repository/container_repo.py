from app.db.async_terminus_client import AsyncClient
from terminusdb_client.woqlquery.woql_query import WOQLQuery as WQ, Doc
from app.core.model.nodes import ThemeConfig
from app.core.model.schemas import ThemeConfigSchema


class ContainerRepo:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def update_basic_info(self, container_id: str, name: str, description: str, icon: str):
        query = WQ().woql_and(
            WQ().update_triple(container_id, "name", WQ().string(name)),
            WQ().update_triple(container_id, "description",  WQ().string(description)),
            # WQ().update_triple(container_id, "icon",  WQ().string(icon)),
        )
        try:
            await self.client.query(query, commit_msg=f"Updating basic info for container {container_id}")
            return True
        except Exception as exc:
            print(exc)
            return False

    async def update_theme_config(self, container_id: str, theme_config: ThemeConfig):
        schema = ThemeConfigSchema.from_pydantic(theme_config)
        query = WQ().woql_and(
            WQ().triple(container_id, "theme_config", "v:old_theme_config"),
            WQ().delete_document("v:old_theme_config"),

            WQ().insert_document(
                Doc(schema._obj_to_dict()[0]), "v:new_theme_config"),
            WQ().update_triple(container_id, "theme_config", "v:new_theme_config"),
        )
        try:
            await self.client.query(query, commit_msg=f"Updating theme config for container {container_id}")
            return True
        except Exception as exc:
            print(exc)
            return False
