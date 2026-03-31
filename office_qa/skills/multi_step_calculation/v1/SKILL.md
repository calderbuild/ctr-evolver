# multi_step_calculation

## Strategy Description
Extract multiple values from Treasury Bulletins and perform precise multi-step calculations. Best for questions requiring sums, differences, percent changes, or ratios across data points.

## Applicable Question Types
- "What was the percent change between X in year A and year B?"
- "What is the absolute difference between X and Y?"
- "What is the total sum of monthly values for year Z?"
- Any question requiring arithmetic on extracted values

## Core Techniques
1. Break the question into sub-problems: what values do I need?
2. Extract each value separately, recording the source file and table
3. Write Python code for ALL calculations -- never do mental math
4. Apply rounding ONLY at the final step, exactly as specified
5. Double-check: does my answer format match what the question asks?

## Examples
Question: "What was the absolute percent change of total defense expenditures between 1940 and 1953?"
Reasoning:
- Need: sum of monthly defense expenditures for 1940, sum for 1953
- Find 1940 data in treasury_bulletin_1941_01.txt (annual summary)
- Find 1953 data in treasury_bulletin_1954_02.txt (annual summary)
- Calculate: abs((sum_1953 - sum_1940) / sum_1940) * 100
- Round to hundredths place, format as "X.XX%"

## Prompt Template
1. List every value I need to extract (be explicit)
2. For each value: which file, which table, which row/column?
3. Extract values and record them with their units
4. Write Python calculation code:
   ```python
   value_a = ...  # from [source]
   value_b = ...  # from [source]
   result = ...   # formula
   final = round(result, N)  # round per question spec
   ```
5. Format answer exactly as requested
