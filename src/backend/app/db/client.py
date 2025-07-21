from arango import ArangoClient
from arango.database import StandardDatabase
from arango.exceptions import ArangoError
from ..config.settings import get_settings

# Global variables to hold the client and connection
_client: ArangoClient | None = None
_db_connection: StandardDatabase | None = None

def get_db() -> StandardDatabase:
    """
    Get a memoized database connection.
    Initializes the client and connection on the first call.
    """
    global _client, _db_connection
    settings = get_settings()

    # Initialize the client if it doesn't exist
    if _client is None:
        _client = ArangoClient(hosts=settings.ARANGO_HOST)

    # If the database name in the settings has changed, or if we are in a test
    # environment, reset the connection.
    if _db_connection is None or _db_connection.name != settings.ARANGO_DB:
        try:
            _db_connection = _client.db(
                settings.ARANGO_DB,
                username=settings.ARANGO_USER,
                password=settings.ARANGO_PASSWORD,
            )
        except ArangoError as e:
            raise ConnectionError(f"Failed to connect to ArangoDB: {e}")
            
    return _db_connection

# For application-level dependency injection, if needed
def get_db_dependency() -> StandardDatabase:
    return get_db()
