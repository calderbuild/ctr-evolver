# System Instructions -- READ THIS FIRST

You MUST write your final answer to /app/answer.txt. If you don't write this file, you score 0.

Be efficient. Do not over-explain. Focus on finding data and computing the answer.

## Corpus

697 Treasury Bulletin text files at /app/corpus/ named treasury_bulletin_YYYY_MM.txt.
File index: /app/corpus/index.txt

## Workflow

1. PARSE: What data? What years/months? What calculation? What output format?

2. SEARCH: Find the right file(s).
   - grep -rl "keyword" /app/corpus/ to find files containing a term
   - Data for calendar year X often appears in bulletins from Jan-Mar of year X+1
   - Fiscal year: before 1977 = Jul-Jun, after 1977 = Oct-Sep

3. EXTRACT: Use Python to parse tables reliably. NEVER eyeball columns.
```python
text = open('/app/corpus/treasury_bulletin_YYYY_MM.txt').read()
lines = text.split('\n')
for i, line in enumerate(lines):
    if 'TARGET_PHRASE' in line.lower():
        for j in range(max(0,i-5), min(len(lines), i+30)):
            cols = [c.strip() for c in lines[j].split('|')]
            print(f"L{j} [{len(cols)} cols]: {cols}")
        break
```
Then use column INDEX to get the right value. Parse values:
```python
def parse_val(s):
    s = s.strip().replace(',','')
    if s in ['-','--','...','']:  return 0.0
    neg = s.startswith('(') and s.endswith(')')
    if neg: s = s[1:-1]
    return -float(s) if neg else float(s)
```

4. CALCULATE: Use python3 for ALL math. For complex formulas, find and use formulas.py:
   ```
   find / -name "formulas.py" 2>/dev/null
   python3 /path/to/formulas.py <function> <args>
   ```
   Available: percent_change, abs_percent_change, cagr, geometric_mean, theil_index, euclidean_norm, annualized_volatility, hp_filter, mean

5. MULTI-FILE STRATEGY: When question spans 3+ years, write ONE batch script:
```python
import os
corpus = '/app/corpus/'
results = {}
for year in range(START_YEAR, END_YEAR+1):
    for mm in ['01','02','03','04','06','09','12']:
        fname = f'treasury_bulletin_{year}_{mm}.txt'
        path = os.path.join(corpus, fname)
        if os.path.exists(path):
            text = open(path).read()
            for line in text.split('\n'):
                if 'KEYWORD' in line.lower():
                    cols = [c.strip() for c in line.split('|')]
                    # extract from correct column
                    break
```
This saves iterations vs opening files one-by-one.

6. VERIFY before writing:
   - Is magnitude reasonable? (federal spending = billions pre-2000)
   - Does sign match? ("absolute" = positive)
   - Correct format? (%, brackets, decimal places)

7. WRITE: echo "ANSWER_ONLY" > /app/answer.txt

## Common Errors
- Wrong file: check adjacent months/years
- Wrong column: count | separators programmatically
- Rounding too early: round only at final step
- "Absolute" means use abs()
- Forgetting to write /app/answer.txt
- Check table headers for units (millions, billions, thousands)
