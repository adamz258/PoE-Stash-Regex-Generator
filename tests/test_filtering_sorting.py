from decimal import Decimal

from core.filtering import filter_items
from core.models import FilterSpec, ItemRecord, SortSpec
from core.sorting import sort_items


def _items():
    return [
        ItemRecord(name="Alpha", tab="t1", quantity=1, total=Decimal("5")),
        ItemRecord(name="Beta", tab="t2", quantity=2, total=Decimal("10")),
        ItemRecord(name="Gamma", tab="t1", quantity=3, total=Decimal("10")),
    ]


def test_filter_tabs_and_thresholds():
    items = _items()
    spec = FilterSpec(
        tabs={"t1"},
        min_total=Decimal("6"),
        max_total=Decimal("12"),
        min_price=Decimal("3"),
        max_price=Decimal("5"),
    )
    filtered = filter_items(items, spec)

    assert [item.name for item in filtered] == ["Gamma"]


def test_filter_top_n():
    items = _items()
    spec = FilterSpec(top_n=1)
    filtered = filter_items(items, spec)

    assert len(filtered) == 1
    assert filtered[0].name == "Beta"


def test_filter_bottom_n():
    items = _items()
    spec = FilterSpec(bottom_n=1)
    filtered = filter_items(items, spec)

    assert len(filtered) == 1
    assert filtered[0].name == "Alpha"


def test_filter_max_quantity():
    items = _items()
    spec = FilterSpec(max_quantity=2)
    filtered = filter_items(items, spec)

    assert [item.name for item in filtered] == ["Alpha", "Beta"]


def test_filter_price_bounds():
    items = _items()
    spec = FilterSpec(min_price=Decimal("4"), max_price=Decimal("6"))
    filtered = filter_items(items, spec)

    assert [item.name for item in filtered] == ["Alpha", "Beta"]


def test_filter_name_contains_case_insensitive():
    items = _items()
    spec = FilterSpec(name_query="alp")
    filtered = filter_items(items, spec)

    assert [item.name for item in filtered] == ["Alpha"]


def test_sort_total_descending():
    items = _items()
    spec = SortSpec(field="total", ascending=False)
    sorted_items = sort_items(items, spec)

    assert [item.name for item in sorted_items] == ["Gamma", "Beta", "Alpha"]


def test_sort_name_ascending():
    items = _items()
    spec = SortSpec(field="name", ascending=True)
    sorted_items = sort_items(items, spec)

    assert [item.name for item in sorted_items] == ["Alpha", "Beta", "Gamma"]
