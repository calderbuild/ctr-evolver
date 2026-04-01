# Corpus Navigation Guide

## File Naming
Files: treasury_bulletin_YYYY_MM.txt (e.g., treasury_bulletin_1941_01.txt)
Total: 697 files spanning 1939-2025
Index: /app/corpus/index.txt

## Date-to-File Mapping
- Monthly data for month M, year Y: check treasury_bulletin_Y_MM.txt
- Annual summary for year Y: check treasury_bulletin_{Y+1}_01.txt or {Y+1}_02.txt or {Y+1}_03.txt
- A bulletin from January 1954 contains data through end of 1953
- Quarterly data (ESF balance sheets): check _03, _06, _09, _12 months
- If question says "10/1960 Bulletin": go to treasury_bulletin_1960_10.txt

## Search Strategy (Fallback Cascade)
Try each step in order. Stop when you find data.

**Step 1 -- Direct lookup**: If question mentions a specific bulletin (e.g., "10/1960 Bulletin"), go directly to that file.

**Step 2 -- Exact phrase grep**:
```bash
grep -rl "exact phrase" /app/corpus/ | head -20
```

**Step 3 -- Keyword grep**: Use 2-3 key terms:
```bash
grep -rl "defense" /app/corpus/ | xargs grep -l "expenditure" | head -20
```

**Step 4 -- Synonym grep**: Replace term with synonyms from table below.

**Step 5 -- Year-range scan**: Write a batch Python script to scan all files in the relevant year range (see system instructions for template).

**Step 6 -- Broad scan**: If still nothing, scan ALL months of the target year AND the following year:
```bash
ls /app/corpus/treasury_bulletin_{YEAR}_{01..12}.txt /app/corpus/treasury_bulletin_{YEAR+1}_{01..03}.txt 2>/dev/null
```

## Synonym Table
| Primary Term | Synonyms |
|-------------|----------|
| expenditure | outlays, spending, disbursements, payments |
| receipts | revenue, collections, income, taxes |
| public debt | gross federal debt, debt outstanding, total debt, national debt |
| national defense | military, defense spending, Department of Defense, armed forces |
| interest | coupon, discount rate, yield, interest rate |
| trust fund | social security, OASI, stabilization fund, ESF |
| internal revenue | tax, customs, excise, duties |
| intergovernmental | grants-in-aid, federal aid, transfer payments, transfers |
| liabilities to foreigners | foreign holdings, foreign-held, foreign liabilities |
| capital movement | capital flow, balance of payments, capital account |
| surplus | excess, positive balance |
| deficit | shortfall, negative balance |
| assets | holdings, investments, reserves |
| gold | gold stock, gold reserve, monetary gold |
| silver | silver stock, silver holdings |
| currency | circulation, notes, coins |

## Data Location Patterns
| Data Type | Where to Find |
|-----------|---------------|
| Annual summary for year Y | bulletins from Jan-Mar of year Y+1 |
| Monthly data | same month's bulletin or next month |
| ESF balance sheet | quarterly: _03, _06, _09, _12 |
| Public debt (monthly) | every month's bulletin |
| Budget summary | typically in _01 or _02 (annual) |
| International transactions | often in _06 or _12 |
| Tax receipts by type | typically in annual summary bulletins |

## When File Not Found
- Try adjacent months: _01, _02, _03 around the target
- Try the NEXT year's bulletins for annual summaries
- For fiscal year data: try the bulletin from the month AFTER fiscal year ends
- List what's available: `ls /app/corpus/treasury_bulletin_YYYY_*.txt`
- If nothing works: widen search to ±2 years
