# System Instructions -- READ THIS FIRST

You MUST write your final answer to /app/answer.txt. If you don't write this file, you score 0.

Be efficient. Do not over-explain. Focus on finding data and computing the answer.

## Step 0: Setup Formula Library

BEFORE doing anything else, create the formula library:
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
    d = [0.0]*n; d[0]=1+lam; d[1]=1+5*lam
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

4. CALCULATE: Use python3 for ALL math. For complex formulas:
   ```
   python3 /tmp/formulas.py <function> <args>
   ```
   Available: percent_change, abs_percent_change, cagr, geometric_mean, theil_index, euclidean_norm, annualized_volatility, hp_filter, mean, log_return, abs_difference

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
