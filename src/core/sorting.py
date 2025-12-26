from typing import Iterable, List

from .models import ItemRecord, SortSpec


def sort_items(items: Iterable[ItemRecord], spec: SortSpec) -> List[ItemRecord]:
    field = spec.field.lower()
    reverse = not spec.ascending

    if field == "name":
        key_func = lambda item: (item.name, item.tab, item.quantity, item.total)
    elif field == "tab":
        key_func = lambda item: (item.tab, item.name, item.quantity, item.total)
    elif field == "quantity":
        key_func = lambda item: (item.quantity, item.name, item.tab, item.total)
    elif field == "total":
        key_func = lambda item: (item.total, item.name, item.tab, item.quantity)
    else:
        raise ValueError(f"Unsupported sort field: {spec.field}")

    return sorted(items, key=key_func, reverse=reverse)
