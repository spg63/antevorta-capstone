import uuid
from abc import abstractmethod


class AbstractSqliteWrapper:
    @abstractmethod
    def __init__(self, filepath: str) -> None:
        pass

    @abstractmethod
    def __del__(self) -> None:
        pass

    @abstractmethod
    def read_bytes_from_db(self, uuid: uuid.UUID) -> bytes | None:
        pass

    @abstractmethod
    def write_bytes_to_db(self, uuid: uuid.UUID, features: tuple[str, ...], data: bytes) -> None:
        pass

    @abstractmethod
    def read_all_entries(self) -> list[bytes] | None:
        pass

    @abstractmethod
    def read_uuids_per_features(self, features: tuple[str, ...]) -> list[uuid.UUID]:
        pass
