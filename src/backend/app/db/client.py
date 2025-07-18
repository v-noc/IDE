from arango import ArangoClient
from arango.database import StandardDatabase
from ..config.settings import settings

# Initialize the ArangoDB client
client = ArangoClient(hosts=settings.ARANGO_HOST)

# Connect to the database
db: StandardDatabase = client.db(
    settings.ARANGO_DB,
    username=settings.ARANGO_USER,
    password=settings.ARANGO_PASSWORD,
)

def get_db() -> StandardDatabase:
    return db
