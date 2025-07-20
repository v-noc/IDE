from arango import ArangoClient
from arango.database import StandardDatabase
from arango.exceptions import ArangoError
from ..config.settings import settings

# Initialize the ArangoDB client
client = ArangoClient(hosts=settings.ARANGO_HOST)
db_connection: StandardDatabase | None = None

def get_db() -> StandardDatabase:
    """Get a memoized database connection with error handling."""
    global db_connection
    if db_connection is None:
        try:
            db_connection = client.db(
                settings.ARANGO_DB,
                username=settings.ARANGO_USER,
                password=settings.ARANGO_PASSWORD,
            )
        except ArangoError as e:
            raise ConnectionError(f"Failed to connect to ArangoDB: {e}")
    return db_connection

# For application-level dependency injection, if needed
def get_db_dependency() -> StandardDatabase:
    return get_db()
