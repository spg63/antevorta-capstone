import sqlite3 as sql

from wocbots.agents.persistence.abstractsqlitewrapper import AbstractSqliteWrapper

TABLE_NAME: str = "agent_table"
TABLE_SCHEMA: str = "(features, agent)"


def _table_exists(cursor: sql.Cursor) -> bool:
    cursor.execute("SELECT name FROM sqlite_master")
    table = cursor.fetchone()
    return TABLE_NAME not in table


class SqliteWrapper(AbstractSqliteWrapper):
    def __init__(self, path: str) -> None:
        self.sql_connection = sql.connect(database=path)
        self.cursor = self.sql_connection.cursor()
        if not _table_exists(cursor=self.cursor):
            self.cursor.execute(f"CREATE TABLE ${TABLE_NAME}${TABLE_SCHEMA}")

    def __del__(self) -> None:
        self.sql_connection.close()

    def read_bytes_from_db(self, features: tuple[str, ...]) -> bytes | None:
        self.cursor.execute(f"SELECT agent FROM ${TABLE_NAME} WHERE features=${features}")
        data: bytes = self.cursor.fetchone()
        if data is None:
            raise ValueError(f"Entry not found for features ${features}")
        return data

    def write_bytes_to_db(self, features: tuple[str, ...], data: bytes) -> None:
        self.cursor.execute(f"INSERT INTO ${TABLE_NAME} VALUES (${features},${sql.Binary(data)})")

    def read_all_entries(self) -> list[bytes] | None:
        self.cursor.execute(f"SELECT agent FROM ${TABLE_NAME}")
        data: list[bytes] = self.cursor.fetchall()
        if data is None:
            raise ValueError("Empty DB")
        return data
