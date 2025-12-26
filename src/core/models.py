from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Iterable, Optional


@dataclass(frozen=True)
class ItemRecord:
    name: str
    tab: str
    quantity: int
    total: Decimal


@dataclass(frozen=True)
class FilterSpec:
    tabs: set[str] = field(default_factory=set)
    name_query: Optional[str] = None
    min_total: Optional[Decimal] = None
    max_total: Optional[Decimal] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    min_quantity: Optional[int] = None
    max_quantity: Optional[int] = None
    top_n: Optional[int] = None
    bottom_n: Optional[int] = None


@dataclass(frozen=True)
class SortSpec:
    field: str
    ascending: bool = True


@dataclass(frozen=True)
class RegexResult:
    entries: list[str]
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None
