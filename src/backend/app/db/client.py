from arango import ArangoClient
from arango.database import StandardDatabase
from arango.exceptions import ArangoError
from ..config.settings import settings

# Initialize the ArangoDB client
client = ArangoClient(hosts=settings.ARANGO_HOST)
db_connection: StandardDatabase | None = None
_db_name_for_connection: str | None = None

def get_db() -> StandardDatabase:
    """Get a memoized database connection with error handling."""
    global db_connection, _db_name_for_connection
    
    # If the database name has changed, reset the connection
    if _db_name_for_connection != settings.ARANGO_DB:
        db_connection = None
        _db_name_for_connection = settings.ARANGO_DB

    if db_connection is None:
        try:
            db_connection = client.db(
                _db_name_for_connection,
                username=settings.ARANGO_USER,
                password=settings.ARANGO_PASSWORD,
            )
        except ArangoError as e:
            raise ConnectionError(f"Failed to connect to ArangoDB: {e}")
    return db_connection

# For application-level dependency injection, if needed
def get_db_dependency() -> StandardDatabase:
    return get_db()
