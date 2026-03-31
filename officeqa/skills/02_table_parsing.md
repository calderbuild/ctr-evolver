# Table Parsing Guide

## Table Structure
Treasury Bulletin tables are Markdown with | separators:
```
| Category | Jan | Feb | Mar | ... | Total |
|----------|-----|-----|-----|-----|-------|
| Revenue  | 123 | 456 | 789 | ... | 1368  |
```

## CRITICAL: Column Identification
1. Find the header row(s) -- there may be 2-3 header rows
2. Count the | separators to determine column positions
3. Use python3 to split: `line.split('|')` and index the right column
4. DO NOT eyeball column alignment -- count separators programmatically

## Python Table Parsing
```python
# Read lines around the target
lines = open('/app/corpus/treasury_bulletin_YYYY_MM.txt').readlines()
# Find header and data rows
for i, line in enumerate(lines):
    if 'keyword' in line.lower():
        cols = [c.strip() for c in line.split('|')]
        print(f"Line {i}: {cols}")
```

## Units
- Check table headers for: "(In millions of dollars)", "(In billions)", "(In thousands)"
- If header says "millions" and you read "1,234", the actual value is 1,234,000,000... NO!
  The value IS 1,234 millions. Only convert if the question asks for a different unit.
- Remove commas before parsing: "1,234" -> 1234

## Special Values
| Symbol | Meaning |
|--------|---------|
| (123) or -123 | Negative 123 |
| - or -- | Zero or not applicable |
| * | See footnote |
| r | Revised value |
| p | Preliminary |
| e | Estimated |
| ... | Data not available |

## Multi-Row Headers
Some tables have headers spanning 2-3 rows. Read ALL header rows to understand what each column represents. Example:
```
|          | Fiscal Year 1953 |              |
| Item     | Budget    | Trust | Total      |
```
Here "Budget" and "Trust" are sub-columns under "Fiscal Year 1953".
