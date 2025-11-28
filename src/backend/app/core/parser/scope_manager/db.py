import kuzu
import os
from pathlib import Path

class DBConnectionManager:
    def __init__(self, project_name: str, db_path: str = None):
        if db_path is None:
            # Default to ~/.v-noc/db/<project_name>
            home = Path.home()
            self.db_path = str(home / ".v-noc" / "db" / project_name)
        else:
            self.db_path = db_path
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.db = kuzu.Database(self.db_path)
        self.conn = kuzu.Connection(self.db)
        self._initialize_schema()

    def _initialize_schema(self):
        # Create Scope Node Table
        # We use 'CREATE NODE TABLE IF NOT EXISTS' logic by checking if table exists first
        # Kuzu doesn't support IF NOT EXISTS for tables in all versions, so we try/except or check catalog.
        # For simplicity in this iteration, we'll try to create and ignore "already exists" error.
        
        try:
            self.conn.execute("""
                CREATE NODE TABLE Scope (
                    id STRING,
                    name STRING,
                    qname STRING,
                    type STRING,
                    file_path STRING,
                    start_line INT64,
                    start_col INT64,
                    end_line INT64,
                    end_col INT64,
                    PRIMARY KEY (id)
                )
            """)
        except RuntimeError as e:
            if "already exists" not in str(e):
                raise e

        # Create CallSite Node Table
        try:
            self.conn.execute("""
                CREATE NODE TABLE CallSite (
                    id STRING,
                    line INT64,
                    col INT64,
                    PRIMARY KEY (id)
                )
            """)
        except RuntimeError as e:
            if "already exists" not in str(e):
                raise e

        # Create Relationships
        # CONTAINS: Scope -> Scope (e.g. Class contains Function)
        try:
            self.conn.execute("CREATE REL TABLE CONTAINS (FROM Scope TO Scope)")
        except RuntimeError as e:
            if "already exists" not in str(e):
                raise e

        # HAS_CALL_SITE: Scope -> CallSite (Caller)
        try:
            self.conn.execute("CREATE REL TABLE HAS_CALL_SITE (FROM Scope TO CallSite)")
        except RuntimeError as e:
            if "already exists" not in str(e):
                raise e

        # TARGETS: CallSite -> Scope (Callee)
        # Note: The target might be a Scope (Function/Class).
        try:
            self.conn.execute("CREATE REL TABLE TARGETS (FROM CallSite TO Scope)")
        except RuntimeError as e:
            if "already exists" not in str(e):
                raise e

    def get_connection(self):
        return self.conn
