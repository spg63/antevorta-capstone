import sqlite3 as sql
import os.path as path

from collections.abc import Sequence

from wocbots.agents.agent import Agent
from wocbots.agents.persistence.abstractsqlitewrapper import AbstractSqliteWrapper

TABLE_NAME : str = "agent_table"
TABLE_SCHEMA : str = "(features, agent)"

def _table_exists(cursor : sql.Cursor) -> bool:
    cursor.execute("SELECT name FROM sqlite_master")
    table = cursor.fetchone()
    if TABLE_NAME not in table:
        return False
    return True

class SqliteWrapper(AbstractSqliteWrapper):
    def __init__(self, path : path) -> None:
        self.sql_connection = sql.connect(database=path)
        self.cursor = self.sql_connection.cursor()
        if not _table_exists(cursor=self.cursor):
            self.cursor.execute(f"CREATE TABLE ${TABLE_NAME}${TABLE_SCHEMA}")

    def __del__(self) -> None:
        self.sql_connection.close()

    def read_bytes_from_db(self, features : tuple[str,...]) -> bytes:
        self.cursor.execute(f"SELECT agent FROM ${TABLE_NAME} WHERE features=${features}")
        data : bytes = self.cursor.fetchone()
        if data == None:
            raise ValueError(f"Entry not found for features ${features}")
        return data

    def write_bytes_to_db(self, features : tuple[str, ...], data : bytes) -> None:
        self.cursor.execute(f"INSERT INTO ${TABLE_NAME} VALUES (${features},${data})")

    def read_all_entries(self) -> list[bytes]:
        self.cursor.execute(f"SELECT agent FROM ${TABLE_NAME}")
        data : list[bytes] = self.cursor.fetchall()
        if data == None:
            raise ValueError("Empty DB")
        return data