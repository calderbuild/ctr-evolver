# Table Parsing Guide

## Table Structure
Treasury Bulletin tables are Markdown with | separators:
```
| Category | Jan | Feb | Mar | ... | Total |
|----------|-----|-----|-----|-----|-------|
| Revenue  | 123 | 456 | 789 | ... | 1368  |
```

## CRITICAL: Column Identification (3-Step Verification)
1. **Print header rows**: Always print the first 5-10 lines of the table to see ALL header rows
2. **Count columns**: Use `line.split('|')` to get column count and index
3. **Cross-verify**: Check your target column value against at least 2 other data rows to confirm the column is correct

```python
# ALWAYS print full header + several data rows before extracting
lines = text.split('\n')
for i, line in enumerate(lines):
    if 'keyword' in line.lower():
        # Print 5 lines before (headers) and 10 after (data)
        for j in range(max(0,i-5), min(len(lines), i+10)):
            cols = [c.strip() for c in lines[j].split('|')]
            print(f"L{j} [{len(cols)} cols]: {cols}")
        break
```

## Value Parsing
```python
def parse_val(s):
    s = s.strip().replace(',','')
    if s in ['-','--','...','','n.a.','N/A','(*)']:  return 0.0
    # Remove footnote markers
    s = s.rstrip('*rpet ')
    neg = s.startswith('(') and s.endswith(')')
    if neg: s = s[1:-1]
    try:
        return -float(s) if neg else float(s)
    except:
        return 0.0  # Unparseable value
```

## Units
- **ALWAYS check table headers** for: "(In millions of dollars)", "(In billions)", "(In thousands)"
- The unit applies to ALL numbers in that table unless noted otherwise
- If header says "millions" and you read "1,234": actual value = 1,234 million dollars
- If question asks "in billions" but data is "in millions": divide by 1000
- If question asks "in millions" but data is "in billions": multiply by 1000
- **Common magnitudes**: Federal spending pre-2000 = billions, post-2010 = trillions

## Special Values
| Symbol | Meaning |
|--------|---------|
| (123) | Negative 123 |
| -123 | Negative 123 |
| - or -- | Zero or not applicable |
| * | See footnote (strip before parsing) |
| r | Revised (strip, use the number) |
| p | Preliminary (strip, use the number) |
| e | Estimated (strip, use the number) |
| ... | Data not available |
| n.a. or N/A | Not available |
| (1) | Could be negative 1 OR footnote ref -- check context |

## Multi-Row Headers
Some tables have 2-3 header rows. Read ALL of them:
```
|          | Fiscal Year 1953 |              |
| Item     | Budget    | Trust | Total      |
```
"Budget" and "Trust" are sub-columns under "Fiscal Year 1953".

## Merged/Spanning Columns
When a table has merged cells, the | count may vary across rows. Always verify column count on EACH row you parse, not just the header.
