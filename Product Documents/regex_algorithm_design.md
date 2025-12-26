# Regex Algorithm Design

## Inputs
- Targets: set of item names selected by the current filters
- Non-targets: all other item names from the loaded CSV
- Max length: 250 characters

## Output
- One or more regex strings that collectively match all targets and match zero non-targets
- If any single required pattern exceeds the max length, return a clear error and no regex

## Constraints and assumptions
- Item names are treated as literal text; output preserves original casing
- Matching is assumed case-insensitive in PoE stash search (subject to revision)
- ^ and $ anchors are assumed to behave as standard line anchors
- Only basic regex constructs are used: literals, grouping, alternation, ^ and $
- Prefer suffix-based matching with $ when safe

## High-level strategy
1. Prefer short, safe suffix patterns that only match targets.
2. Detect cases where suffix-only matching cannot disambiguate.
3. Use anchored full-name patterns for those cases.
4. Assemble a compact regex and validate it against the dataset.
5. Enforce max length; fail safely if exceeded.

## Detailed steps

### 1) Preprocessing
- Build target set T and non-target set N from the dataset.
- Escape regex metacharacters in names: . ^ $ * + ? ( ) [ ] { } | \
- Keep a stable ordering of names for deterministic output.
- Normalize names to a comparable form (e.g., lowercased) for collision checks.

### 2) Suffix index
- For each name in T and N, generate all character suffixes.
- Build a map: suffix -> {target_count, non_target_count, covered_targets}
- A suffix is "safe" if non_target_count == 0.

### 3) Suffix-impossible detection
- If a target name is a suffix of any non-target name, then no suffix-only
  regex can separate it. Mark it as "needs_exact".
- Example from the sample: "Orb of Annulment" is a suffix of
  "Eldritch Orb of Annulment".

### 4) Candidate generation
- For each safe suffix, create a candidate pattern: <escaped_suffix> + "$".
- Each candidate covers all targets that end with that suffix.
- For each "needs_exact" target, create an exact pattern:
  "^" + <escaped_full_name> + "$".

### 5) Candidate selection (greedy set cover)
- Maintain a set of uncovered targets.
- Repeatedly select the candidate that covers the most uncovered targets.
- Tie-break deterministically by:
  1) Shortest pattern length
  2) Lexicographic order of the raw suffix
- Mark covered targets and continue until all are covered.

### 6) Regex assembly
- Combine selected patterns with alternation: pattern1|pattern2|...
- Keep a stable pattern ordering (length, then lexicographic) for determinism.
- Compute final length; if > max length, attempt compaction:
  - Build a reverse trie of selected suffixes and emit a grouped regex to
    factor shared trailing substrings.
  - Use only grouping and alternation, e.g., "(foo|ba(r|z))$".
- If still too long, split patterns into multiple regex strings, each <= max length.
  - Use deterministic packing (greedy fill by pattern length, then lexicographic).
  - If any single pattern exceeds max length, return an error state.

### 7) Collision validation
- Run a collision check over the loaded dataset for each regex entry:
  - All targets are covered by at least one entry
  - Zero non-targets may match any entry
  - Use case-insensitive matching in validation
- If validation fails, return an error and no regex.

## Determinism
- All set iterations are replaced with sorted lists.
- Tie-breakers are explicit and stable.
- Numeric parsing uses Decimal to avoid nondeterministic sorting.
- Regex splitting uses deterministic ordering and packing.
