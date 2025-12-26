import argparse
import sys
from decimal import Decimal, InvalidOperation

from core.config import DEFAULT_MATCH_MODE, MAX_REGEX_LENGTH
from core.csv_loader import load_csv
from core.filtering import filter_items
from core.models import FilterSpec, SortSpec
from core.regex_generator import generate_regex
from core.sorting import sort_items


def _parse_decimal(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        raise argparse.ArgumentTypeError(f"Invalid decimal value: {value}")


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value: {value}")


def _parse_tabs(value: str | None) -> set[str]:
    if not value:
        return set()
    return {tab.strip() for tab in value.split(",") if tab.strip()}


def _build_non_targets(all_items, selected_items) -> list[str]:
    selected_ids = {id(item) for item in selected_items}
    return [item.name for item in all_items if id(item) not in selected_ids]


def _quote_regex(regex: str) -> str:
    return f'"{regex}"'


def _max_raw_regex_length() -> int:
    return max(1, MAX_REGEX_LENGTH - 2)


def main() -> int:
    parser = argparse.ArgumentParser(description="PoE Stash Regex Generator CLI")
    parser.add_argument("--csv", required=True, help="Path to CSV export")
    parser.add_argument("--tabs", help="Comma-separated tab names")
    parser.add_argument("--name-contains", help="Substring match against item names")
    parser.add_argument("--min-total", type=_parse_decimal)
    parser.add_argument("--max-total", type=_parse_decimal)
    parser.add_argument("--min-price", type=_parse_decimal)
    parser.add_argument("--max-price", type=_parse_decimal)
    parser.add_argument("--min-quantity", type=_parse_int)
    parser.add_argument("--max-quantity", type=_parse_int)
    parser.add_argument("--top-n", type=_parse_int, help="Top X items by total value")
    parser.add_argument("--bottom-n", type=_parse_int, help="Bottom X items by total value")
    parser.add_argument(
        "--sort-field",
        choices=["name", "tab", "quantity", "total"],
        help="Sort field",
    )
    parser.add_argument("--sort-desc", action="store_true")
    parser.add_argument(
        "--match-mode",
        choices=["exact", "balanced", "compact"],
        default=DEFAULT_MATCH_MODE,
        help="Regex matching mode",
    )
    parser.add_argument("--show-warnings", action="store_true")

    args = parser.parse_args()

    records, warnings = load_csv(args.csv)
    if args.show_warnings and warnings:
        for warning in warnings:
            print(f"WARN: {warning}", file=sys.stderr)

    spec = FilterSpec(
        tabs=_parse_tabs(args.tabs),
        name_query=args.name_contains.strip() if args.name_contains else None,
        min_total=args.min_total,
        max_total=args.max_total,
        min_price=args.min_price,
        max_price=args.max_price,
        min_quantity=args.min_quantity,
        max_quantity=args.max_quantity,
        top_n=args.top_n,
        bottom_n=args.bottom_n,
    )

    filtered = filter_items(records, spec)
    if args.sort_field:
        filtered = sort_items(
            filtered,
            SortSpec(field=args.sort_field, ascending=not args.sort_desc),
        )

    targets = [item.name for item in filtered]
    non_targets = _build_non_targets(records, filtered)

    result = generate_regex(
        targets,
        non_targets,
        max_length=_max_raw_regex_length(),
        match_mode=args.match_mode,
    )

    print(f"Loaded items: {len(records)}")
    print(f"Filtered items: {len(filtered)}")

    if not result.ok:
        print(f"ERROR: {result.error}")
        return 1

    for index, entry in enumerate(result.entries, start=1):
        quoted = _quote_regex(entry)
        print(f"Entry {index} ({len(quoted)} chars): {quoted}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
