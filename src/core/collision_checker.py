import re
from typing import Iterable, Tuple

from .config import CASE_INSENSITIVE_MATCHING


def validate_regex(
    regex_entries: Iterable[str],
    targets: Iterable[str],
    non_targets: Iterable[str],
    case_insensitive: bool = CASE_INSENSITIVE_MATCHING,
) -> Tuple[bool, str | None]:
    entries = [entry for entry in regex_entries if entry]
    if not entries:
        return False, "No regex entries generated."

    flags = re.IGNORECASE if case_insensitive else 0
    compiled = []
    for entry in entries:
        try:
            compiled.append(re.compile(entry, flags))
        except re.error as exc:
            return False, f"Invalid regex '{entry}': {exc}"

    targets_list = list(targets)
    non_targets_list = list(non_targets)

    for name in targets_list:
        if not any(regex.search(name) for regex in compiled):
            return False, f"Regex does not match target '{name}'."

    for name in non_targets_list:
        if any(regex.search(name) for regex in compiled):
            return False, f"Regex matches non-target '{name}'."

    return True, None
