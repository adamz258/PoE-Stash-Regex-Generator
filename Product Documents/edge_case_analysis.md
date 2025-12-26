# Edge Case Analysis (sample_export.csv)

## Dataset shape
- Rows: 514
- Unique item names: 514 (no duplicates)
- Unique tabs: 10
- Missing values in Name/Tab/Quantity/Total: none in the sample

## CSV parsing hazards
- Item names can contain commas inside quotes (example: "Brush, Paint and Palette"), so split-by-comma parsing is unsafe.
- The file uses quoted fields and includes an empty Price column. Parsers must tolerate empty fields.

## Character and formatting variety
- Non-alphanumeric characters observed in names: apostrophe ('), dash (-), slash (/), comma (,).
- Names with digits and slashes: "Wrath - 21/0 corrupted", "Elemental Hit of the Spectrum - 20/20".
- Names with apostrophes: "Hinekora's Lock", "Maven's Chisel of Scarabs".
- Long names up to 44 characters (e.g., "Concentrated Effect Support - 1/23 corrupted").

## Regex collision risks from suffix-only matching
The sample includes names that are suffixes of longer names. For these cases, any suffix-only regex for the shorter name will also match the longer name.

Examples found:
- "Orb of Annulment" vs "Eldritch Orb of Annulment"
- "Chromatic Orb" vs "Tainted Chromatic Orb"
- "Orb of Fusing" vs "Tainted Orb of Fusing"
- "Orb of Augmentation" vs "Foulborn Orb of Augmentation"
- "Temple Map" vs "Crimson/Ivory/Moon Temple Map"
- "Burial Chambers Map" vs "Blighted Burial Chambers Map"
- "Scarab of Stability" vs "Essence Scarab of Stability"

Implication: the generator must support anchored full-name or prefix-based patterns (e.g., ^...$) when suffix-only matching is unsafe.

## High-collision suffixes
Common last words in names:
- Map (87), Orb (31), Scarab (20), Oil (15), corrupted (15)

Common last two words:
- Delirium Orb (13), Temple Map (4), Distant Memory (4), "- 20/20" (9)

Implication: aggressive suffix shortening will cause collisions unless checked against non-targets.

## Numeric parsing quirks
- Totals include long decimal tails (example: 902.6999999999999). Use Decimal or stable rounding to keep sorting/filtering deterministic.

## Tab name variability
- Tabs can include non-alphanumeric characters such as '/' (example: "tatts/runes"). Treat tab names as free text and filter by exact match.
