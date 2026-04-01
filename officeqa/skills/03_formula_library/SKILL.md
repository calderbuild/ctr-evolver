# Formula Library

For ALL calculations, use python3. The formula library is created at /tmp/formulas.py by the setup step in system instructions.

## Usage
```bash
python3 /tmp/formulas.py <function_name> <args...>
```

## Available Functions

### percent_change(old, new, decimals)
((new - old) / old) * 100
```bash
python3 /tmp/formulas.py percent_change 100 150 2
# Output: 50.00
```

### abs_percent_change(old, new, decimals)
abs((new - old) / old) * 100
```bash
python3 /tmp/formulas.py abs_percent_change 150 100 2
# Output: 33.33
```

### cagr(start_value, end_value, years, decimals)
Compound Annual Growth Rate: (end/start)^(1/years) - 1, as percentage
```bash
python3 /tmp/formulas.py cagr 100 200 10 2
# Output: 7.18
```

### geometric_mean(*values, decimals)
(v1 * v2 * ... * vn)^(1/n)
```bash
python3 /tmp/formulas.py geometric_mean 1.5 2.0 1.8 --decimals 3
# Output: 1.748
```

### theil_index(*values, decimals)
Theil's T index for inequality measurement
```bash
python3 /tmp/formulas.py theil_index 100 200 300 400 --decimals 3
```

### euclidean_norm(*values, decimals)
sqrt(sum(v^2 for v in values))
```bash
python3 /tmp/formulas.py euclidean_norm 3 4 --decimals 2
# Output: 5.00
```

### annualized_volatility(*returns, decimals, periods_per_year)
From log returns, compute realized volatility annualized
```bash
python3 /tmp/formulas.py annualized_volatility 0.02 -0.01 0.03 --decimals 2 --periods 52
```

### hp_filter(values_csv, lambda_param, decimals)
Hodrick-Prescott filter, returns trend component
```bash
python3 /tmp/formulas.py hp_filter "100,200,150,300,250" 100 2
```

### mean(*values, decimals)
Simple arithmetic mean
```bash
python3 /tmp/formulas.py mean 10 20 30 --decimals 2
# Output: 20.00
```

### log_return(p1, p2, decimals)
Natural log return: ln(p2/p1)

### abs_difference(a, b, decimals)
Absolute difference: |a - b|

## Inline Python (for simple cases)
```bash
python3 -c "print(round(((150-100)/100)*100, 2))"
```
