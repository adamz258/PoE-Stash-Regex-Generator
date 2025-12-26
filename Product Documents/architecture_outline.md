# Architecture Outline

## Goals
- Headless core logic with deterministic output and full automated test coverage.
- GUI acts as a thin shell around core services.
- No internet dependency; all data is local.

## Proposed tech stack (initial recommendation)
- Language: Python 3.12
- GUI: PySide6 (Qt)
- Tests: pytest
- Persistence: JSON file stored under the app data directory

Rationale: fast iteration, strong string tooling, easy test isolation, and mature desktop GUI support. JSON keeps persistence simple and transparent. If larger scale or schema evolution is needed later, move to SQLite without changing core APIs.

## Core modules (headless)
- core/models.py
  - ItemRecord, Dataset, FilterSpec, SortSpec, RegexResult
- core/csv_loader.py
  - Robust CSV parsing (quoted fields, commas in values, BOM handling)
  - Type coercion for Quantity (int) and Total (Decimal)
- core/filtering.py
  - Tab filter, min total, min quantity, top-N selection
- core/sorting.py
  - Deterministic sorting by name, tab, quantity, total
- core/regex_generator.py
  - Build collision-safe regex within a max length
  - Split into multiple entries when total length exceeds 250
  - Prefers suffix-based matches when safe
- core/collision_checker.py
  - Validates regex against target and non-target names (case-insensitive)
- core/persistence.py
  - Save/load regex entries with labels and metadata
- core/config.py
  - Central config (max regex length=250, storage path)

## GUI layer (thin shell)
- ui/main_window.py
  - File picker, data grid, filter controls, regex preview, save/copy
- ui/view_models.py
  - Binds UI state to core filters and results
- adapters/clipboard.py
  - Clipboard write abstraction used by GUI

## Data flow
1. User selects CSV file.
2. csv_loader parses into ItemRecord list.
3. filtering + sorting produce a current view subset.
4. regex_generator builds one or more regex entries for selected items.
5. collision_checker validates before display/copy.
6. persistence saves/reloads regex entries.

## Determinism guarantees
- Stable sort keys and consistent tie-breakers.
- Regex generator uses deterministic candidate ordering and selection.
- All numeric parsing uses Decimal to avoid float drift.
