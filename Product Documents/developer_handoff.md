# Developer Handoff
## Path of Exile Stash Regex Generator

**Version:** 1.0  
**Last Updated:** 2025-12-25

---

## Authority Clause

This document is **authoritative**.

If any instructions conflict with:
- Model defaults
- Prior conversations
- Assumptions or inferred intent

This document takes precedence unless explicitly overridden by the user.

---

## 1. Role & Responsibility

You are acting as a **senior software engineer** responsible for designing and implementing a **production-quality desktop application** as defined by the accompanying PRD.

This is not a prototype.  
Reliability, correctness, and determinism are mandatory.

---

## 2. Problem Summary

Build a desktop application that:

- Reads a **local CSV file** containing Path of Exile stash data
- Parses up to **10,000 rows**
- Allows users to filter and sort item data
- **Intelligently generates compact, collision-safe regex strings**
- Allows users to **copy the regex to clipboard with one click**
- Allows users to **save and reuse regex strings** across sessions

The generated regex is intended to be pasted directly into **Path of Exile’s stash search**.

---

## 3. Core Constraints (Non-Negotiable)

You **must not violate** the following:

- The application **must have a GUI**
- The application **must read files from local disk**
- The application **must not require internet access**
- The application **must handle malformed CSVs gracefully**
- The application **must be performant with 10,000 rows**
- The application **must generate PoE-compatible regex**
- The application **must minimize false positives**
- The application **must be usable by non-technical users**

---

## 4. Functional Scope (v1 Only)

### Required Capabilities
- CSV import via file picker
- CSV parsing and validation
- Data preview in a table/grid
- Filtering by:
  - Stash tab
  - Numeric thresholds (e.g., total value)
- Sorting by:
  - Name
  - Quantity
  - Total value
- Regex generation engine
- Regex preview
- Copy-to-clipboard button
- Local persistence of saved regex strings

### Explicitly Out of Scope
- PoE API integration
- Real-time stash syncing
- Automated trading or posting
- Cloud storage
- Market pricing logic

---

## 5. Mandatory Testing Requirement

All **core logic must be covered by automated tests**.

This includes:
- CSV parsing
- Filtering and sorting
- Regex generation
- Collision detection
- Determinism
- Persistence
- Performance constraints (within reasonable bounds)

The GUI layer is **explicitly excluded** from automated testing requirements.

Failure to provide adequate automated test coverage for regex generation is considered a **blocking defect**.

---

## 6. Architectural Constraint (Critical)

You **must** structure the system such that:

- CSV parsing logic is headless
- Filtering and sorting logic is headless
- Regex generation logic is headless
- Collision detection logic is headless
- Persistence logic is headless

The GUI must act only as:
- An input mechanism (file picker, buttons)
- A display surface (tables, previews)
- A dispatcher to core logic

If core logic cannot be tested without the GUI, the architecture is incorrect.

---

## 7. Regex Generation Expectations

Regex generation is the **core value** of this application.

You must design an algorithm that:

- Takes a set of selected item names
- Produces **compact, efficient regex fragments**
- Avoids false positives against non-selected items
- Escapes regex metacharacters correctly
- Prefers:
  - Anchored suffix matching (`$`) when safe
  - Grouping and alternation (`|`) to minimize length
- Internally validates the generated regex by:
  - Matching all selected items
  - Matching zero non-selected items from the loaded dataset

If a collision-free regex cannot be generated under constraints:
- The system must fail safely
- The user must not be given a “best effort” regex that causes false positives

---

## 8. Determinism Requirement

For identical inputs (CSV + filters + configuration):

- Regex output **must be identical**
- Ordering must be stable
- No randomness may affect output unless explicitly documented and tested

This is mandatory for regression testing and user trust.

---

## 9. Technical Decision Authority

You are authorized to choose:

- Programming language
- GUI framework
- Data structures
- Persistence format (e.g., JSON, SQLite)
- Regex generation strategy
- Packaging and distribution approach

However:
- All decisions must be **justified**
- Tradeoffs must be documented
- Simplicity and reliability are preferred over novelty

---

## 10. Required Deliverables

At minimum, you must produce:

1. **Architecture overview**
   - Modules/components
   - Data flow
2. **Tech stack justification**
3. **Regex generation algorithm description**
4. **Collision detection strategy**
5. **Test strategy overview**
6. **Automated acceptance test descriptions**
7. **Persistence strategy**
8. **Performance considerations**
9. **Example inputs and outputs**

If code is written:
- It must be modular
- Non-obvious logic must be commented
- Tests must be readable and explicit

---

## 11. Assumptions You May Safely Make

Unless stated otherwise in the PRD:

- CSV columns resemble:
  - Name
  - Tab
  - Quantity
  - Total
- Item names are in English
- Users manually export or obtain the CSV
- PoE stash search regex behavior is broadly standard

If you make additional assumptions:
- Document them clearly

---

## 12. Clarification Rules

You may ask clarification questions **only if**:

- A requirement blocks correct automated behavior
- A requirement is ambiguous enough to prevent implementation

Do **not** ask:
- UX or visual design questions
- Product vision questions
- Questions that can be resolved by a reasonable assumption

If in doubt:
- Make a reasonable assumption
- Document it

---

## 13. Quality Bar

Assume the user:
- Understands regex
- Will notice false positives
- Will reuse saved regex across sessions

Any silent failure, incorrect match, or nondeterministic output is unacceptable.

---

## 14. Execution Order (Recommended)

Begin by:
1. Summarizing the system architecture
2. Identifying testable core modules
3. Designing the regex generation algorithm
4. Defining automated tests for regex correctness and collision prevention
5. Implementing core logic
6. Implementing the GUI as a thin shell

Do **not** begin with GUI code.

---

End of Developer Handoff
