# Implementation Plan

## Phase 1: Project setup
1. Create repo structure:
   - src/core
   - src/ui
   - tests
2. Add tooling config:
   - pytest.ini
   - basic lint config (optional)
3. Define config constants (max regex length = 250).

## Phase 2: Core data model and CSV parsing
1. Implement ItemRecord, FilterSpec, SortSpec, RegexResult.
2. Implement csv_loader:
   - Robust CSV parsing with BOM handling and quoted fields.
   - Graceful handling of missing/invalid Quantity/Total.
   - Use Decimal for Total to avoid float drift.
3. Unit tests for parsing edge cases.

## Phase 3: Filtering and sorting
1. Implement filter functions:
   - Tab selection (exact match)
   - Min total, min quantity
   - Top-N by total
2. Implement deterministic sorting with stable tie-breakers.
3. Unit tests for each filter/sort option.

## Phase 4: Regex generation engine
1. Implement regex escaping and suffix index builder.
2. Implement suffix-safe candidate generation and exact-match fallback.
3. Implement greedy set-cover selection with deterministic tie-breakers.
4. Implement optional reverse-trie compaction.
5. Enforce max length and split into multiple regex entries when needed.
6. Use case-insensitive collision checks during validation.
7. Unit tests:
   - All targets match, zero non-targets match
   - Suffix-collision cases (e.g., Orb of Annulment vs Eldritch Orb of Annulment)
   - Deterministic output for identical inputs
   - Multi-entry split behavior when total length exceeds 250

## Phase 5: Collision checking
1. Implement collision_checker using Python re.
2. Add tests for collision failures and error messaging.

## Phase 6: Persistence
1. Implement JSON storage for saved regex entries:
   - label, regex string, filters used, timestamp
2. Unit tests for save/load round-trip and corrupted data handling.

## Phase 7: GUI shell
1. Build PySide6 UI:
   - File picker, data grid, filters, regex preview
   - Generate, copy, save, and saved-list controls
2. Wire UI to core modules with a simple view-model layer.
3. Manual smoke test with sample_export.csv.

## Phase 8: Performance validation
1. Generate a synthetic 10,000-row CSV.
2. Run parsing, filtering, and regex generation benchmarks.
3. Add performance tests with reasonable time thresholds.

## Phase 9: Packaging and release
1. Package with PyInstaller (Windows).
2. Provide a minimal README and usage notes.

## Acceptance checkpoints
- Core tests pass and cover regex generation and collision checking.
- Regex output is deterministic and <= 250 chars per entry, split automatically when needed.
- GUI is functional but thin; core logic remains headless.
