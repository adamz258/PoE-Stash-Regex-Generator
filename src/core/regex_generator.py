from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

from .collision_checker import validate_regex
from .config import (
    CASE_INSENSITIVE_MATCHING,
    DEFAULT_MATCH_MODE,
    MAX_REGEX_LENGTH,
    MIN_MULTI_WORD_SUFFIX_LENGTH,
    MIN_SINGLE_WORD_SUFFIX_LENGTH,
)
from .models import RegexResult

REGEX_META = set(".^$*+?()[]{}|\\")


def _escape_literal(text: str) -> str:
    return "".join(f"\\{char}" if char in REGEX_META else char for char in text)


def _escape_char(char: str) -> str:
    return f"\\{char}" if char in REGEX_META else char


def _normalize(name: str, case_insensitive: bool) -> str:
    return name.lower() if case_insensitive else name


def _iter_suffixes(text: str) -> Iterable[str]:
    for index in range(len(text)):
        yield text[index:]


def _is_balanced_suffix(
    raw_suffix: str,
    min_single_word_length: int,
    min_multi_word_length: int,
) -> bool:
    if not raw_suffix or raw_suffix[0] == " ":
        return False
    if " " in raw_suffix:
        return len(raw_suffix) >= min_multi_word_length
    return len(raw_suffix) >= min_single_word_length


def _build_suffix_set(names: Iterable[str]) -> set[str]:
    suffixes: set[str] = set()
    for name in names:
        for suffix in _iter_suffixes(name):
            suffixes.add(suffix)
    return suffixes


def _has_suffix_relations(strings: List[str]) -> bool:
    ordered = sorted(strings, key=len)
    for index, short in enumerate(ordered):
        for long_value in ordered[index + 1 :]:
            if long_value.endswith(short):
                return True
    return False


def _build_suffix_regex(strings: List[str]) -> str:
    groups: dict[str, List[str]] = {}
    for value in strings:
        if not value:
            raise ValueError("Empty string is not supported for suffix compaction.")
        groups.setdefault(value[-1], []).append(value[:-1])

    parts: List[str] = []
    for char in sorted(groups.keys()):
        prefixes = groups[char]
        if prefixes and all(value == "" for value in prefixes):
            subpattern = ""
        else:
            subpattern = _build_suffix_regex(sorted(prefixes)) if prefixes else ""
        if subpattern:
            parts.append(subpattern + _escape_char(char))
        else:
            parts.append(_escape_char(char))

    if len(parts) == 1:
        return parts[0]
    return "(" + "|".join(parts) + ")"


def _compact_suffixes(raw_suffixes: List[str]) -> Optional[str]:
    unique = sorted(set(raw_suffixes))
    if len(unique) <= 1:
        return None
    if any(value == "" for value in unique):
        return None
    if _has_suffix_relations(unique):
        return None

    regex_body = _build_suffix_regex(unique)
    return f"({regex_body})$"


@dataclass
class Candidate:
    key: str
    pattern: str
    covers: set[int]
    is_suffix: bool


def _pack_patterns(patterns: List[str], max_length: int) -> Tuple[Optional[List[str]], Optional[str]]:
    if max_length <= 0:
        return None, "Max length must be positive."

    ordered = sorted(patterns, key=lambda value: (len(value), value))
    entries: List[str] = []
    current = ""

    for pattern in ordered:
        if len(pattern) > max_length:
            return None, f"Single pattern exceeds max length: '{pattern}'."

        if not current:
            current = pattern
            continue

        if len(current) + 1 + len(pattern) <= max_length:
            current = f"{current}|{pattern}"
        else:
            entries.append(current)
            current = pattern

    if current:
        entries.append(current)

    return entries, None


def _pack_exact_names(names: List[str], max_length: int) -> Tuple[Optional[List[str]], Optional[str]]:
    ordered = sorted(names, key=lambda value: (len(value), value))
    entries: List[str] = []
    current = ""

    for name in ordered:
        single = f"^{name}$"
        if len(single) > max_length:
            return None, f"Single pattern exceeds max length: '{single}'."

        if not current:
            current = name
            continue

        candidate = f"{current}|{name}"
        grouped = f"^(?:{candidate})$"
        if len(grouped) <= max_length:
            current = candidate
        else:
            if "|" in current:
                entries.append(f"^(?:{current})$")
            else:
                entries.append(f"^{current}$")
            current = name

    if current:
        if "|" in current:
            entries.append(f"^(?:{current})$")
        else:
            entries.append(f"^{current}$")

    return entries, None


def generate_regex(
    target_names: Iterable[str],
    non_target_names: Iterable[str],
    max_length: int = MAX_REGEX_LENGTH,
    case_insensitive: bool = CASE_INSENSITIVE_MATCHING,
    match_mode: str = DEFAULT_MATCH_MODE,
    min_single_word_length: int = MIN_SINGLE_WORD_SUFFIX_LENGTH,
    min_multi_word_length: int = MIN_MULTI_WORD_SUFFIX_LENGTH,
) -> RegexResult:
    targets_raw = sorted({name for name in target_names if name})
    non_targets_raw = sorted({name for name in non_target_names if name})

    if not targets_raw:
        return RegexResult(entries=[], error="No targets provided.")

    targets_norm = {_normalize(name, case_insensitive) for name in targets_raw}
    non_targets_norm = {_normalize(name, case_insensitive) for name in non_targets_raw}

    overlap = targets_norm & non_targets_norm
    if overlap:
        example = sorted(overlap)[0]
        return RegexResult(
            entries=[],
            error=(
                "Target and non-target names overlap under case-insensitive matching: "
                f"'{example}'."
            ),
        )

    if match_mode == "exact":
        escaped = [_escape_literal(name) for name in targets_raw]
        entries, error = _pack_exact_names(escaped, max_length)
        if error:
            return RegexResult(entries=[], error=error)

        ok, validation_error = validate_regex(entries, targets_raw, non_targets_raw, case_insensitive)
        if not ok:
            return RegexResult(entries=[], error=validation_error)

        return RegexResult(entries=entries, error=None)

    if match_mode not in {"compact", "balanced"}:
        return RegexResult(entries=[], error=f"Unsupported match mode: {match_mode}")

    non_target_suffixes = _build_suffix_set(non_targets_norm)

    candidate_map: dict[str, set[int]] = {}
    representative_raw: dict[str, str] = {}
    needs_exact: set[int] = set()

    for index, raw in enumerate(targets_raw):
        normalized = _normalize(raw, case_insensitive)
        if normalized in non_target_suffixes:
            needs_exact.add(index)

        positions = list(range(len(raw)))
        for pos in positions:
            suffix_raw = raw[pos:]
            if match_mode == "balanced":
                if not _is_balanced_suffix(suffix_raw, min_single_word_length, min_multi_word_length):
                    continue
            suffix_norm = normalized[pos:]
            if suffix_norm in non_target_suffixes:
                continue
            candidate_map.setdefault(suffix_norm, set()).add(index)

            existing = representative_raw.get(suffix_norm)
            if existing is None or suffix_raw < existing:
                representative_raw[suffix_norm] = suffix_raw

    if candidate_map:
        covered_targets = set().union(*candidate_map.values())
    else:
        covered_targets = set()

    for index in range(len(targets_raw)):
        if index not in covered_targets:
            needs_exact.add(index)

    candidates: List[Candidate] = []
    for suffix_norm, cover in candidate_map.items():
        raw_suffix = representative_raw[suffix_norm]
        pattern = f"{_escape_literal(raw_suffix)}$"
        candidates.append(
            Candidate(
                key=raw_suffix,
                pattern=pattern,
                covers=cover,
                is_suffix=True,
            )
        )

    for index in needs_exact:
        raw = targets_raw[index]
        pattern = f"^{_escape_literal(raw)}$"
        candidates.append(
            Candidate(
                key=raw,
                pattern=pattern,
                covers={index},
                is_suffix=False,
            )
        )

    uncovered = set(range(len(targets_raw)))
    selected: List[Candidate] = []

    while uncovered:
        best: Optional[Candidate] = None
        best_cover: set[int] = set()

        for candidate in candidates:
            cover = candidate.covers & uncovered
            if not cover:
                continue
            if best is None:
                best = candidate
                best_cover = cover
                continue

            if len(cover) > len(best_cover):
                best = candidate
                best_cover = cover
                continue
            if len(cover) == len(best_cover):
                if len(candidate.pattern) < len(best.pattern):
                    best = candidate
                    best_cover = cover
                    continue
                if len(candidate.pattern) == len(best.pattern) and candidate.key < best.key:
                    best = candidate
                    best_cover = cover

        if best is None:
            return RegexResult(
                entries=[],
                error="Unable to cover all targets with collision-safe patterns.",
            )

        selected.append(best)
        uncovered -= best_cover

    suffix_candidates = [candidate for candidate in selected if candidate.is_suffix]
    exact_patterns = [candidate.pattern for candidate in selected if not candidate.is_suffix]

    suffix_patterns = [candidate.pattern for candidate in suffix_candidates]
    if len(suffix_candidates) > 1:
        compacted = _compact_suffixes([candidate.key for candidate in suffix_candidates])
        if compacted:
            combined_length = sum(len(pattern) for pattern in suffix_patterns) + (len(suffix_patterns) - 1)
            if len(compacted) < combined_length and len(compacted) <= max_length:
                suffix_patterns = [compacted]

    all_patterns = suffix_patterns + exact_patterns
    if not all_patterns:
        return RegexResult(entries=[], error="No patterns could be generated.")

    entries, error = _pack_patterns(all_patterns, max_length)
    if error:
        return RegexResult(entries=[], error=error)

    ok, validation_error = validate_regex(entries, targets_raw, non_targets_raw, case_insensitive)
    if not ok:
        return RegexResult(entries=[], error=validation_error)

    return RegexResult(entries=entries, error=None)
