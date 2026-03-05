from terminusdb_client.errors import DatabaseError
from app.core.model.schemas import ProjectSchema, BaseSchema, TerminusBase
from app.db.woqlschema import *
from app.db.client import get_db, get_settings
import asyncio


async def migrate_db():
    """
    Migrate the database from the old schema to the new schema.
    """
    client = await get_db()
    # print(await client.get_database(client.db))
    schema_obj = WOQLSchema(
        title="V-NOC Schema",
        description="V-NOC code analysis graph schema",
        authors=["V-NOC Team"],
    )
    schema_obj.add_obj(TerminusBase.__name__, TerminusBase)
    schema_obj.add_obj(BaseSchema.__name__, BaseSchema)
    schema_obj.add_obj(ProjectSchema.__name__, ProjectSchema)
    await schema_obj.commit(client, "Add ProjectSchema to schema", full_replace=True)


async def get_all_documents():
    client = await get_db()
    documents = await client.get_all_documents(graph_type=GraphType.SCHEMA.value)
    for document in documents:
        print(document)
    return documents


async def get_database(db_name: str):
    try:
        client = await get_db()
        return await client.create_database("test_db")
    except DatabaseError as e:
        print(f"Error getting database: {e.error_obj.get("api:error", "")}")
        return None

if __name__ == "__main__":
    asyncio.run(get_database("tada"))
