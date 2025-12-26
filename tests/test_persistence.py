from core.persistence import load_entries, new_entry, save_entries


def test_persistence_round_trip(tmp_path):
    path = tmp_path / "saved.json"
    entry = new_entry("Test", ["foo", "bar"], {"tab": "c"})

    save_entries(str(path), [entry])
    loaded, warnings = load_entries(str(path))

    assert not warnings
    assert len(loaded) == 1
    assert loaded[0].label == "Test"
    assert loaded[0].entries == ["foo", "bar"]


def test_persistence_handles_corruption(tmp_path):
    path = tmp_path / "saved.json"
    path.write_text("{not valid json", encoding="ascii")

    loaded, warnings = load_entries(str(path))

    assert loaded == []
    assert warnings
