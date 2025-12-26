from decimal import Decimal

from core.csv_loader import load_csv


def test_load_csv_parses_and_defaults(tmp_path):
    csv_text = (
        '"Name","Tab","Quantity","Total"\n'
        '"Brush, Paint and Palette","div","","abc"\n'
        '"Valid Item","tab","3","1.5"\n'
    )
    path = tmp_path / "sample.csv"
    path.write_text(csv_text, encoding="utf-8")

    records, warnings = load_csv(str(path))

    assert len(records) == 2
    assert records[0].name == "Brush, Paint and Palette"
    assert records[0].quantity == 1
    assert records[0].total == Decimal("0")
    assert records[1].quantity == 3
    assert records[1].total == Decimal("1.5")
    assert warnings


def test_load_csv_skips_missing_name(tmp_path):
    csv_text = (
        '"Name","Tab","Quantity","Total"\n'
        '"","tab","2","10"\n'
        '"Valid Item","tab","2","10"\n'
    )
    path = tmp_path / "sample.csv"
    path.write_text(csv_text, encoding="utf-8")

    records, warnings = load_csv(str(path))

    assert len(records) == 1
    assert records[0].name == "Valid Item"
    assert warnings
