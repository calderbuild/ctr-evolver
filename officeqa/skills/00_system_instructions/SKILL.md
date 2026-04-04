# System Instructions -- READ THIS FIRST

You MUST write your final answer to /app/answer.txt. If you don't write this file, you score 0.

IMPORTANT: Be extremely concise. Do NOT explain reasoning. Do NOT repeat the question. Do NOT narrate what you are doing. Output ONLY commands and their results. Every extra token wastes time and money.

## Step 0: Setup

Run this FIRST, before anything else:
```bash
cat > /tmp/formulas.py << 'PYEOF'
import math, sys

def percent_change(old, new, decimals=2):
    return round(((new - old) / old) * 100, decimals)

def abs_percent_change(old, new, decimals=2):
    return round(abs((new - old) / old) * 100, decimals)

def cagr(start_value, end_value, years, decimals=2):
    return round(((end_value / start_value) ** (1 / years) - 1) * 100, decimals)

def geometric_mean(*values, decimals=3):
    product = 1.0
    for v in values: product *= v
    return round(product ** (1 / len(values)), decimals)

def theil_index(*values, decimals=3):
    n = len(values); mu = sum(values) / n
    return round(sum((v/mu)*math.log(v/mu) for v in values if v>0)/n, decimals)

def euclidean_norm(*values, decimals=2):
    return round(math.sqrt(sum(v**2 for v in values)), decimals)

def annualized_volatility(*returns, decimals=2, periods_per_year=52):
    n = len(returns)
    if n == 0: return 0.0
    realized_var = sum(r**2 for r in returns) / n
    return round(math.sqrt(realized_var * periods_per_year) * 100, decimals)

def hp_filter(values, lam=100, decimals=2):
    n = len(values)
    if n < 3: return [round(v, decimals) for v in values]
    d=[0.0]*n; d[0]=1+lam; d[1]=1+5*lam
    for i in range(2,n-2): d[i]=1+6*lam
    d[n-2]=1+5*lam; d[n-1]=1+lam
    dl=[0.0]*n; dl[1]=-2*lam
    for i in range(2,n-1): dl[i]=-4*lam
    dl[n-1]=-2*lam
    dll=[0.0]*n
    for i in range(2,n): dll[i]=lam
    y=list(values)
    for i in range(1,n):
        if d[i-1]==0: continue
        m=dl[i]/d[i-1]; d[i]-=m*dl[i]; y[i]-=m*y[i-1]; dl[i]=0
        if i>=2:
            m2=dll[i]/d[i-2] if d[i-2]!=0 else 0
            d[i]-=m2*dll[i]; y[i]-=m2*y[i-2]; dll[i]=0
    trend=[0.0]*n; trend[n-1]=y[n-1]/d[n-1] if d[n-1]!=0 else y[n-1]
    for i in range(n-2,-1,-1): trend[i]=y[i]/d[i] if d[i]!=0 else y[i]
    return [round(t,decimals) for t in trend]

def mean(*values, decimals=2):
    return round(sum(values)/len(values), decimals)

def log_return(p1, p2, decimals=6):
    return round(math.log(p2/p1), decimals)

def abs_difference(a, b, decimals=2):
    return round(abs(a-b), decimals)

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args: print("Usage: python3 /tmp/formulas.py <func> <args>"); sys.exit(0)
    func = globals().get(args[0])
    if not func: print(f"Unknown: {args[0]}"); sys.exit(1)
    pos=[]; kw={}; i=1
    while i<len(args):
        if args[i].startswith("--"):
            kw[args[i][2:]]=float(args[i+1]); i+=2
        else:
            v=args[i]
            if "," in v: pos.append([float(x) for x in v.split(",")])
            else:
                try: pos.append(float(v))
                except: pos.append(v)
            i+=1
    if args[0]=="hp_filter":
        vals=pos[0] if isinstance(pos[0],list) else pos
        print(hp_filter(vals,int(kw.get("lambda",pos[1] if len(pos)>1 else 100)),int(kw.get("decimals",pos[2] if len(pos)>2 else 2))))
    elif args[0] in ("geometric_mean","theil_index","euclidean_norm","annualized_volatility","mean"):
        dec=int(kw.get("decimals",3)); per=int(kw.get("periods",52))
        if args[0]=="annualized_volatility": print(annualized_volatility(*pos,decimals=dec,periods_per_year=per))
        else: print(func(*pos,decimals=dec))
    else:
        if len(pos)>=2: *vals,dec=pos; print(func(*[float(v) for v in vals],int(dec)))
        else: print(func(*[float(x) for x in pos]))
PYEOF
```

## Corpus

697 Treasury Bulletin text files at /app/corpus/ named treasury_bulletin_YYYY_MM.txt.
File index: /app/corpus/index.txt

## Workflow

### 1. PARSE the question
Extract these from the question text:
- **Topic keywords**: what data (expenditures, debt, receipts, ESF, discount rate, etc.)
- **Time range**: specific months/years, fiscal years, calendar years
- **Calculation**: percent change, CAGR, mean, geometric mean, Theil index, etc.
- **Output format**: decimal places, %, brackets, units (millions/billions)
- **Hints**: if question mentions a specific bulletin date (e.g., "10/1960 Bulletin"), go directly to that file

### 2. SEARCH for files
- If question specifies a bulletin date: go directly to treasury_bulletin_YYYY_MM.txt
- Otherwise: `grep -rl "keyword" /app/corpus/ | head -20`
- Data for calendar year X often appears in bulletins from Jan-Mar of year X+1
- Fiscal year: before 1977 = Jul-Jun, after 1977 = Oct-Sep
- **If grep returns nothing**: try synonyms. "expenditure"="outlays"="spending", "receipts"="revenue"="collections", "public debt"="gross federal debt"="debt outstanding"

### 3. EXTRACT data with Python
NEVER eyeball columns. ALWAYS use Python to parse:
```python
text = open('/app/corpus/treasury_bulletin_YYYY_MM.txt').read()
lines = text.split('\n')
matches = []
for i, line in enumerate(lines):
    if 'TARGET_PHRASE' in line.lower():
        matches.append(i)
# Show context around ALL matches, not just the first
for m in matches:
    print(f"\n=== Match at line {m} ===")
    for j in range(max(0,m-5), min(len(lines), m+30)):
        cols = [c.strip() for c in lines[j].split('|')]
        print(f"L{j} [{len(cols)} cols]: {cols}")
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

### 4. CALCULATE with Python
Use python3 for ALL math. For complex formulas:
```
python3 /tmp/formulas.py <function> <args>
```
Available: percent_change, abs_percent_change, cagr, geometric_mean, theil_index, euclidean_norm, annualized_volatility, hp_filter, mean, log_return, abs_difference

For simple math, use: `python3 -c "print(round(EXPR, N))"`

### 5. MULTI-FILE strategy
When question spans multiple years/months, write ONE batch Python script:
```python
import os, re
corpus = '/app/corpus/'
results = {}
# Scan ALL months -- some data only appears in certain months
for year in range(START_YEAR, END_YEAR+2):  # +2 to catch data published later
    for mm in range(1, 13):
        fname = f'treasury_bulletin_{year}_{mm:02d}.txt'
        path = os.path.join(corpus, fname)
        if not os.path.exists(path):
            continue
        text = open(path).read()
        for i, line in enumerate(text.split('\n')):
            if 'KEYWORD' in line.lower():
                cols = [c.strip() for c in line.split('|')]
                # Extract value from correct column index
                # results[key] = parse_val(cols[COL_IDX])
                break
print(results)
```
This saves iterations vs opening files one-by-one.

### 6. VERIFY before writing
- Is magnitude reasonable? (federal spending in billions pre-2000, trillions post-2010)
- Does sign match? ("absolute" means use abs())
- Correct unit? Check table header for "millions", "billions", "thousands"
- Correct format? (decimal places, %, brackets)
- If answer seems wildly off, re-check which column you extracted from

### 7. WRITE the answer
```bash
echo "ANSWER_ONLY" > /app/answer.txt
```
**OUTPUT RULES**:
- Write ONLY the final numeric value. No text, no explanation, no units.
- Do NOT write unit words ("million", "billion", "thousand") -- just the number.
- Do NOT write "$" -- just the number.
- Do NOT write stray numbers (dates, line numbers, page refs) -- ONLY the answer.
- "in billions" → write "8.124" not "8.124 billion"
- "as a percent" → write "12.34%" (include % only when asked)
- Lists: [val1, val2, val3] with comma+space
- Round ONLY at the final step

## Common Errors to Avoid
- Wrong file: data for year X may be in year X+1 bulletins
- Wrong column: count | separators PROGRAMMATICALLY, never by eye
- Rounding too early: round ONLY at final output step
- "Absolute" means take abs() of the result
- Forgetting to write /app/answer.txt -- always write it
- Wrong units: check table header (millions vs billions vs thousands)
- Searching too narrowly: try synonym terms if first grep fails
- Not checking adjacent months when data isn't in expected file
- Including unit words in answer -- just write the number
