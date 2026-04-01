# Corpus Navigation Guide

## File Naming
Files: treasury_bulletin_YYYY_MM.txt (e.g., treasury_bulletin_1941_01.txt)
Total: 697 files spanning 1939-2025
Index: /app/corpus/index.txt

## Date-to-File Mapping
- Monthly data for month M, year Y: check treasury_bulletin_Y_MM.txt
- Annual summary for year Y: check treasury_bulletin_{Y+1}_01.txt or {Y+1}_02.txt
- A bulletin from January 1954 contains data through end of 1953

## Search Strategy
1. First: grep -rl "exact phrase" /app/corpus/ (find which files contain the term)
2. Then: grep -n "exact phrase" /app/corpus/treasury_bulletin_YYYY_MM.txt (find line numbers)
3. Then: read around those line numbers to get the full table

## Search Terms by Topic
| Topic | Search Terms |
|-------|-------------|
| Spending | "expenditure", "outlays", "disbursements" |
| Revenue | "receipts", "revenue", "collections" |
| Debt | "public debt", "debt outstanding", "gross federal debt" |
| Defense | "national defense", "military", "Department of Defense" |
| Interest | "interest", "coupon", "discount rate" |
| Trust funds | "trust fund", "social security", "stabilization fund" |
| Taxes | "internal revenue", "customs", "tax" |
| Grants | "intergovernmental", "grants-in-aid", "federal aid" |

## When File Not Found
- Try adjacent months: if treasury_bulletin_1954_02.txt doesn't have it, try _01 or _03
- Try the following year's bulletins for annual summaries
- Some topics appear in specific monthly bulletins (e.g., ESF balance sheet in quarterly months)
