from decimal import Decimal
from typing import Iterable, List

from .models import FilterSpec, ItemRecord


def _price_for(item: ItemRecord) -> Decimal:
    if item.quantity <= 0:
        return Decimal("0")
    return item.total / Decimal(item.quantity)


def filter_items(items: Iterable[ItemRecord], spec: FilterSpec) -> List[ItemRecord]:
    filtered = list(items)

    if spec.tabs:
        filtered = [item for item in filtered if item.tab in spec.tabs]

    if spec.name_query:
        query = spec.name_query.casefold()
        filtered = [item for item in filtered if query in item.name.casefold()]

    if spec.min_total is not None:
        filtered = [item for item in filtered if item.total >= spec.min_total]

    if spec.max_total is not None:
        filtered = [item for item in filtered if item.total <= spec.max_total]

    if spec.min_price is not None:
        filtered = [item for item in filtered if _price_for(item) >= spec.min_price]

    if spec.max_price is not None:
        filtered = [item for item in filtered if _price_for(item) <= spec.max_price]

    if spec.min_quantity is not None:
        filtered = [item for item in filtered if item.quantity >= spec.min_quantity]

    if spec.max_quantity is not None:
        filtered = [item for item in filtered if item.quantity <= spec.max_quantity]

    if spec.top_n is not None:
        filtered = sorted(
            filtered,
            key=lambda item: (-item.total, item.name, item.tab, item.quantity),
        )[: spec.top_n]

    if spec.bottom_n is not None:
        filtered = sorted(
            filtered,
            key=lambda item: (item.total, item.name, item.tab, item.quantity),
        )[: spec.bottom_n]

    return filtered
