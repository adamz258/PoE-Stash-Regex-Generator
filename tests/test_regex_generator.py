from core.regex_generator import generate_regex


def test_suffix_collision_forces_exact():
    targets = ["Orb of Annulment"]
    non_targets = ["Eldritch Orb of Annulment"]

    result = generate_regex(targets, non_targets)

    assert result.ok
    assert any("^Orb of Annulment$" in entry or "^(?:Orb of Annulment)$" in entry for entry in result.entries)


def test_case_insensitive_overlap_fails():
    targets = ["Chaos Orb"]
    non_targets = ["chaos orb"]

    result = generate_regex(targets, non_targets)

    assert not result.ok
    assert "overlap" in (result.error or "").lower()


def test_split_when_exceeds_max_length():
    targets = ["Alpha", "Beta", "Gammx"]
    non_targets = []

    result = generate_regex(targets, non_targets, max_length=8, match_mode="compact")

    assert result.ok
    assert len(result.entries) >= 1
    assert all(len(entry) <= 8 for entry in result.entries)


def test_deterministic_output():
    targets_a = ["Horned Scarab of Awakening", "Horned Scarab of Pandemonium"]
    targets_b = list(reversed(targets_a))
    non_targets = ["Scarab of Pandemonium"]

    result_a = generate_regex(targets_a, non_targets)
    result_b = generate_regex(targets_b, non_targets)

    assert result_a.entries == result_b.entries
