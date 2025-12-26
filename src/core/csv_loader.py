import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Tuple

from .config import CSV_ENCODING, DEFAULT_QUANTITY, DEFAULT_TOTAL
from .models import ItemRecord


def _parse_int(value: str, default: int, warnings: list[str], row_index: int, field_name: str) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        warnings.append(
            f"Row {row_index}: invalid {field_name} '{value}', defaulting to {default}."
        )
        return default


def _parse_decimal(value: str, default: Decimal, warnings: list[str], row_index: int, field_name: str) -> Decimal:
    if value is None or value == "":
        return default
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError):
        warnings.append(
            f"Row {row_index}: invalid {field_name} '{value}', defaulting to {default}."
        )
        return default


def load_csv(path: str) -> Tuple[list[ItemRecord], list[str]]:
    records: list[ItemRecord] = []
    warnings: list[str] = []

    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    with csv_path.open(newline="", encoding=CSV_ENCODING) as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            warnings.append("CSV appears to be empty or missing headers.")
            return records, warnings

        for row_index, row in enumerate(reader, start=2):
            name = (row.get("Name") or "").strip()
            if not name:
                warnings.append(f"Row {row_index}: missing Name, row skipped.")
                continue

            tab = (row.get("Tab") or "").strip()
            quantity = _parse_int(row.get("Quantity") or "", DEFAULT_QUANTITY, warnings, row_index, "Quantity")
            total = _parse_decimal(row.get("Total") or "", DEFAULT_TOTAL, warnings, row_index, "Total")

            records.append(
                ItemRecord(
                    name=name,
                    tab=tab,
                    quantity=quantity,
                    total=total,
                )
            )

    return records, warnings
