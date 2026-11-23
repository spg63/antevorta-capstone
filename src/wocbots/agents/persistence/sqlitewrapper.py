import os
import sqlite3 as sql
import uuid

from wocbots.agents.persistence.abstractsqlitewrapper import AbstractSqliteWrapper

TABLE_NAME: str = "agent_table"
TABLE_SCHEMA: str = "(uuid TEXT, features TEXT, agent BLOB)"


def _table_exists(cursor: sql.Cursor) -> bool:
    cursor.execute("SELECT name FROM sqlite_master")
    tables = [table[0] for table in cursor.fetchall()]
    return TABLE_NAME in tables


class SqliteWrapper(AbstractSqliteWrapper):
    def __init__(self, path: str) -> None:
        if not os.path.exists(path):
            with open(path, "a"):
                pass
        self.sql_connection = sql.connect(database=path, autocommit=True)
        self.cursor = self.sql_connection.cursor()
        if not _table_exists(cursor=self.cursor):
            self.cursor.execute(f"CREATE TABLE {TABLE_NAME}{TABLE_SCHEMA}")

    def __del__(self) -> None:
        self.sql_connection.close()

    def read_bytes_from_db(self, uuid: uuid.UUID) -> bytes | None:
        self.cursor.execute(
            f"SELECT agent FROM {TABLE_NAME} WHERE uuid=?",
            (str(uuid)),
        )
        data_tuple: bytes = self.cursor.fetchone()
        if data_tuple is None:
            raise ValueError(f"Entry not found for uuid {uuid}")
        return bytes(data_tuple[0])

    def write_bytes_to_db(self, uuid: uuid.UUID, features: tuple[str, ...], data: bytes) -> None:
        self.cursor.execute(
            f"INSERT INTO {TABLE_NAME} VALUES (?, ?, ?)",
            (str(uuid), str(features), sql.Binary(data)),
        )

    def read_all_entries(self) -> list[bytes] | None:
        self.cursor.execute(f"SELECT agent FROM {TABLE_NAME}")
        data: list[bytes] = [bytes_tuple[0] for bytes_tuple in self.cursor.fetchall()]
        if data is None:
            raise ValueError("Empty DB")
        return data

    def read_uuids_per_features(self, features: tuple[str, ...]) -> list[uuid.UUID]:
        self.cursor.execute(
            f"SELECT uuid FROM {TABLE_NAME} WHERE features=?",
            (str(features)),
        )
        data: list[uuid.UUID] | None = self.cursor.fetchall()
        if data is None:
            raise ValueError(f"No matching agents for features {features}")
        return data
