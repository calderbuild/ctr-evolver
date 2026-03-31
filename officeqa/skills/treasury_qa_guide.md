# Treasury Bulletin QA Quick Reference

## File Search Patterns
- Expenditure/spending: grep for "expenditure" or "outlays"
- Revenue: grep for "receipts" or "revenue"  
- Debt: grep for "public debt" or "outstanding"
- Defense: grep for "national defense" or "military"
- Intergovernmental: grep for "intergovernmental" or "grants"
- Exchange Stabilization Fund: grep for "stabilization fund" or "ESF"

## Reading Tables
- Tables use | as column separators
- Headers may span 2-3 rows — read ALL header rows before extracting data
- Units are in headers: "(In millions of dollars)", "(In billions)"
- Footnotes: r = revised, p = preliminary, e = estimated, * = see note
- (123) means negative 123, dash (-) means zero

## Date Logic
- WW1: 1914-1918 (US entry 1917)
- WW2: 1939-1945 (US entry Dec 1941)  
- Korean War: 1950-1953
- Fiscal year changed 1977: before=Jul-Jun, after=Oct-Sep
- Data for calendar year X: check bulletins from Jan-Mar of year X+1 for annual summaries

## Calculation Templates
```
# Percent change
python3 -c "old=VALUE1; new=VALUE2; print(round(((new-old)/old)*100, DECIMALS))"

# Absolute percent change  
python3 -c "old=VALUE1; new=VALUE2; print(round(abs((new-old)/old)*100, DECIMALS))"

# Sum monthly values
python3 -c "vals=[v1,v2,...,v12]; print(round(sum(vals), DECIMALS))"

# Absolute difference
python3 -c "a=VALUE1; b=VALUE2; print(round(abs(a-b), DECIMALS))"
```
