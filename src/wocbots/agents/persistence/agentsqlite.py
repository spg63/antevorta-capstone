import sqlite3 as sql
import os.path as path

from collections.abc import Sequence

TABLE_NAME : str = "agent_table"
TABLE_SCHEMA : str = "(features, agent)"

def _table_exists(cursor : sql.Cursor) -> bool:
    cursor.execute("SELECT name FROM sqlite_master")
    table = cursor.fetchone()
    if TABLE_NAME not in table:
        return False
    return True

class AgentSqlite:
    def __init__(self, path : path):
        self.sql_connection = sql.connect(database=path)
        self.cursor = self.sql_connection.cursor()
        if not _table_exists(cursor=self.cursor):
            self.cursor.execute(f"CREATE TABLE ${TABLE_NAME}${TABLE_SCHEMA}")

    def __del__(self):
        self.sql_connection.close()

    def read_bytes_from_db(self, features : tuple[str,...]) -> bytes:
        self.cursor.execute(f"SELECT agent FROM ${TABLE_NAME} WHERE features=${features}")
        data : bytes = self.cursor.fetchone()
        return data

    def write_bytes_to_db(self, features : tuple[str, ...], data : bytes) -> None:
        self.cursor.execute(f"INSERT INTO ${TABLE_NAME} VALUES (${features},${data})")

    