# src/db/helper.py

from dataclasses import dataclass
from typing import NotRequired, TypedDict, Union

from pymongo import ASCENDING


class IndexOptions(TypedDict):
    unique: NotRequired[bool]
    sparse: NotRequired[bool]
    name: NotRequired[str]


@dataclass
class IndexConfig:
    key: str
    order: Union[int, str] = ASCENDING
    unique: bool = False
    sparse: bool = False
    index_name: str = ""

    def to_index_spec(
        self,
    ) -> tuple[list[tuple[str, Union[int, str]]], IndexOptions]:
        """Converts the IndexConfig to a format suitable for MongoDB index creation."""
        order_str = str(self.order).replace(" ", "_")
        name = (
            self.index_name
            or f"{self.key}_{order_str}_{'unique' if self.unique else 'idx'}"
        )

        return [(self.key, self.order)], {"unique": self.unique, "name": name}
