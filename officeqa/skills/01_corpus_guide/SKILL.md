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

## Search Strategy
1. First: `grep -rl "exact phrase" /app/corpus/ | head -20` (find files)
2. Then: `grep -n "exact phrase" /app/corpus/treasury_bulletin_YYYY_MM.txt` (find lines)
3. Then: read around those line numbers with Python to get the full table

## Synonym Search -- If First Search Fails
| Primary Term | Try Also |
|-------------|----------|
| expenditure | outlays, spending, disbursements |
| receipts | revenue, collections, income |
| public debt | gross federal debt, debt outstanding, total debt |
| national defense | military, defense spending, Department of Defense |
| interest | coupon, discount rate, yield |
| trust fund | social security, stabilization fund, ESF |
| internal revenue | tax, customs, excise |
| intergovernmental | grants-in-aid, federal aid, transfer payments |
| liabilities to foreigners | foreign holdings, foreign-held |
| capital movement | capital flow, balance of payments |

## When File Not Found
- Try adjacent months: if _02 doesn't have it, try _01 or _03
- Try the NEXT year's bulletins for annual summaries
- For fiscal year data: try the bulletin from the month AFTER fiscal year ends
- Some topics only appear in certain months (ESF in quarterly bulletins)
- List available files: `ls /app/corpus/treasury_bulletin_YYYY_*.txt`
