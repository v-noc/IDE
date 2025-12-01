import kuzu
import os

import platformdirs as pl


class DBConnectionManager:
    def __init__(self, project_name: str, db_path: str = None):
        if db_path is None:
            # Match legacy layout using app data dir per project
            db_dir = os.path.join(pl.user_data_dir("v-noc"), "kuzu_db")
            self.db_path = os.path.join(db_dir, project_name)
        else:
            self.db_path = db_path

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        print(f"Database path: {self.db_path}")
        self.db = kuzu.Database(self.db_path)
        self.conn = kuzu.Connection(self.db)
        self._initialize_schema()

    def _initialize_schema(self):
        # Create Scope node table (ignore "already exists" errors)

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
                    mro STRING[],
                    checksum STRING,
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
                    name STRING,
                    PRIMARY KEY (id)
                )
            """)
        except RuntimeError as e:
            if "already exists" not in str(e):
                raise e

        # Create Relationships
        # CONTAINS: Scope -> Scope (e.g. Class contains Function)
        try:
            self.conn.execute(
                "CREATE REL TABLE CONTAINS (FROM Scope TO Scope)")
        except RuntimeError as e:
            if "already exists" not in str(e):
                raise e

        # HAS_CALL_SITE: Scope -> CallSite (Caller)
        try:
            self.conn.execute(
                "CREATE REL TABLE HAS_CALL_SITE (FROM Scope TO CallSite)")
        except RuntimeError as e:
            if "already exists" not in str(e):
                raise e

        # TARGETS: CallSite -> Scope (Callee)
        try:
            self.conn.execute(
                "CREATE REL TABLE TARGETS (FROM CallSite TO Scope)")
        except RuntimeError as e:
            if "already exists" not in str(e):
                raise e

        # NEXT_IN_CHAIN: CallSite -> CallSite (Call chain)
        try:
            self.conn.execute(
                "CREATE REL TABLE NEXT_IN_CHAIN (FROM CallSite TO CallSite)")
        except RuntimeError as e:
            if "already exists" not in str(e):
                raise e

    def get_connection(self):
        return self.conn
