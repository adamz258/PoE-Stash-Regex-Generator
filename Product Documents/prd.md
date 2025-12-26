# Product Requirements Document (PRD)
## Path of Exile Stash Regex Generator

**Version:** 1.0  
**Last Updated:** 2025-12-25

---

## 1. Overview

### 1.1 Product Name (Working)
**PoE Stash Regex Generator**

### 1.2 Summary
A desktop application that reads a **local CSV export of Path of Exile stash data**, intelligently analyzes item names and metadata, and generates **compact, collision-safe regex strings** that players can copy and paste into **Path of Exile’s stash search** to quickly locate valuable items for sale on the in-game currency exchange.

---

## 2. Problem Statement

Path of Exile players who engage in bulk selling or currency exchange frequently need to:

- Manually search stash tabs for valuable items
- Copy/paste long lists of item names
- Rebuild searches repeatedly as stash contents change
- Avoid false positives caused by partial name matches

PoE’s stash search supports **regex**, but:
- Writing efficient regex is non-trivial
- Long regex strings become unmanageable
- Poorly constructed patterns cause collisions and false matches

There is currently **no reliable tool** that:
- Reads stash data from CSV
- Intelligently generates **minimal, safe regex**
- Supports reuse and iteration over time

---

## 3. Goals & Success Criteria

### 3.1 Goals
- Enable players to **instantly generate efficient regex** from stash data
- Reduce time spent searching stash tabs for tradeable items
- Eliminate regex collisions and false positives
- Support repeat workflows across leagues and sessions

### 3.2 Non-Goals
- Direct API integration with Path of Exile
- Automatic posting of items for trade
- Real-time stash syncing
- Price checking or market analysis (out of scope for v1)

---

## 4. Core Use Case

1. User exports or obtains a **local CSV file** containing stash data
2. User opens the application
3. User loads the CSV from disk
4. User filters or selects:
   - Specific stash tabs (e.g. `frag`)
   - Value thresholds (e.g. high-value items)
5. Application:
   - Analyzes item names
   - Generates **compact regex fragments**
   - Avoids collisions and false positives
6. User clicks **Copy to Clipboard**
7. User pastes regex directly into PoE stash search
8. User optionally saves the regex for reuse later

---

## 5. Sample Input (CSV)

~~~csv
"Name","Tab","Quantity","Price","Total"
"Mirror of Kalandra","c","2","","219138"
"Hinekora's Lock","c","2","","41200"
"Mirror Shard","c","10","","54270"
"Dark Temptation","div","1","","1408"
"Tattoo of the Arohongui Shaman","tatts/runes","1","","1162"
"Horned Scarab of Pandemonium","frag","3","","902.6999999999999"
"Horned Scarab of Awakening","frag","5","","1244"
~~~

### Example Output (Illustrative Only)
~~~regex
monium$|kening$
~~~

> The above is illustrative and not a strict implementation requirement.

---

## 6. Functional Requirements

### 6.1 File Handling
- Must read **local CSV files** from disk
- Must support CSVs up to **10,000 rows**
- Must gracefully handle:
  - Missing columns
  - Empty fields
  - Unexpected quoting or delimiters
  - Non-numeric values in numeric columns
- Must not modify the source file

### 6.2 Data Parsing & Normalization
- Must parse the following fields (column names may be configurable later):
  - `Name` (string)
  - `Tab` (string)
  - `Quantity` (integer, default 1 if missing/unparseable)
  - `Total` (float or integer; treat as numeric value used for sorting/filtering)
- Must trim whitespace and preserve punctuation in item names
- Must preserve original casing (unless PoE stash search is known to be case-insensitive; do not assume)

### 6.3 Filtering
- Must allow filtering by:
  - Tab name (exact match and/or multi-select)
  - Minimum total value threshold
  - Minimum quantity threshold (optional but supported)
- Must allow “Top N” selection by total value (optional but supported)

### 6.4 Sorting
- Must support sorting by:
  - Total value (ascending/descending)
  - Quantity (ascending/descending)
  - Name (A–Z / Z–A)
  - Tab (A–Z / Z–A)
- Sorting must be deterministic.

### 6.5 Regex Generation (Core)
- Must generate **compact regex** for a selected subset of items.
- Must prioritize correctness:
  - **No false positives** against non-selected items in the loaded dataset (see testing section).
  - **No false negatives** for selected items.
- Must escape regex metacharacters present in names (e.g. `. ^ $ * + ? ( ) [ ] { } | \`).
- Must support and prefer:
  - Suffix-based matching with `$` when safe
  - Grouping and alternation (`|`) to reduce length
- Must provide an internal collision-check method to validate the generated regex against:
  - Selected items (must match)
  - Non-selected items (must not match)

### 6.6 Regex Storage / Reuse (Persistence)
- Must allow users to save regex strings locally.
- Saved entries must include at minimum:
  - A user-defined name/label
  - The regex string
  - Optional metadata (filters used, creation timestamp) if convenient
- Must allow selecting a saved regex and copying it again later.
- Storage must be local-only (file or embedded DB).

### 6.7 Clipboard
- Must provide a single button to **Copy to Clipboard**.
- Clipboard must contain **only** the raw regex string (no extra whitespace, no markdown, no quotes).

---

## 7. Non-Functional Requirements

### 7.1 Reliability
- Must not crash on malformed CSVs or unexpected data
- Must surface clear, user-readable error messages
- Must be deterministic for identical inputs and configuration

### 7.2 Performance
- Must handle CSV parsing for 10,000 rows quickly and keep UI responsive
- Regex generation must complete quickly for typical datasets
- Avoid O(n²) or worse scaling where possible (especially in regex generation)

### 7.3 Usability
- GUI required
- No programming knowledge required
- Regex preview must be visible before copying
- “Saved regex” list must be easy to browse and reuse

### 7.4 Portability
- Windows required
- macOS/Linux optional (nice-to-have)

---

## 8. Technical Considerations

### 8.1 Implementation Language / Framework
- The implementation language/framework is flexible and should be chosen for:
  - Reliability
  - Strong string + regex tooling
  - Good GUI toolkit support
  - Practical packaging/distribution

Examples (non-binding):
- Python + PySide/PyQt
- .NET (WPF / MAUI)
- Rust + Tauri
- Electron + TypeScript

### 8.2 Architecture Constraint
- Core logic (CSV parse, filter/sort, regex generation, collision checks, persistence) must be implemented in **headless modules** independent of the GUI so it can be automated-tested.

---

## 9. UX / UI (High-Level)

Required UI elements:
- File picker to select CSV
- Data preview grid/table
- Filter controls (Tab, thresholds, etc.)
- Sort controls (or sortable table columns)
- Regex preview text area
- Buttons:
  - Generate Regex
  - Copy to Clipboard
  - Save Regex
- Saved regex list (select → preview → copy)

---

## 10. Risks & Open Questions
- CSV schema variations across sources/tools
- Maximum regex length tolerated by PoE stash search
- Handling highly similar item names without collisions
- Unicode/localization issues in item names

---

## 11. Future Enhancements (Out of Scope for v1)
- League-aware presets
- Import/export of saved regex collections
- Regex validation against external or larger catalogs
- Pricing automation or live market integration
- PoE API integration (if permitted)

---

## 12. Open Sections for Future Elaboration
- Exact CSV schema guarantees and optional columns
- Explicit “high value” rules (threshold vs top-N vs category-based)
- Regex style preference (suffix-only vs mixed strategies)
- Maximum acceptable regex length and splitting behavior (if any)
- Whether users can manually edit regex before saving
- Distribution format preference (installer vs portable)

---

## 13. Testing & Automated Acceptance Criteria (Required)

This section defines **automated, machine-verifiable acceptance criteria only**.  
Manual UX testing is out of scope and will be handled separately.

### 13.1 Testing Philosophy
- Core logic must be headless and deterministic
- Tests must run locally without internet access
- GUI code is excluded from automated coverage requirements

### 13.2 CSV Parsing Tests
Automated tests must verify:
- Correct parsing of required columns (`Name`, `Tab`, `Quantity`, `Total`) when present
- Graceful handling of:
  - Missing columns
  - Empty fields
  - Invalid numeric values
  - Malformed rows
- The application does not crash on invalid input
- Parsing performance is acceptable for 10,000 rows

### 13.3 Filtering & Sorting Tests
Automated tests must verify:
- Filtering by tab includes only matching rows
- Filtering by thresholds (e.g., min total value) is correct
- Sorting by name/quantity/total is correct and deterministic

### 13.4 Regex Generation Correctness (Critical)
Given:
- A set of selected (target) item names
- A set of non-selected item names from the same loaded dataset

Automated tests must verify:
- Generated regex matches **100%** of target names
- Generated regex matches **0%** of non-target names
- Special characters are escaped correctly
- Anchors (e.g. `$`) behave as intended
- Output is deterministic (same input → same output)
- Output is compatible with PoE stash-search regex expectations

### 13.5 Collision Avoidance
Automated tests must verify:
- No unintended matches across tabs or filters within the dataset
- If a collision-free regex cannot be produced under constraints, the system fails safely with a clear error state (no silent “best-effort” regex that causes false positives)

### 13.6 Regex Efficiency Constraints
Automated tests must verify:
- Regex length stays within a configurable maximum (default TBD later)
- Redundant patterns are not emitted
- Runtime does not degrade pathologically as inputs grow

### 13.7 Persistence Tests
Automated tests must verify:
- Saved regex entries round-trip correctly:
  - Save → reload → identical content
- Persistence survives application restart
- Corrupted persistence data is handled safely (no crash)

### 13.8 Clipboard Output Tests
Automated tests must verify:
- Clipboard output contains only the regex string
- Clipboard output matches the preview exactly

### 13.9 Performance Tests
Automated tests must verify:
- Bounded execution time for parsing and regex generation at 10,000 rows
- No unbounded memory growth during processing

### 13.10 Coverage Expectations
- Core logic must have high test coverage
- Regex generation and collision checking must be fully covered
- GUI code coverage is not required

---

End of PRD
