# Answer Formatting Rules

## CRITICAL: Write to /app/answer.txt
```bash
echo "YOUR_ANSWER" > /app/answer.txt
```

## Scoring
- Fuzzy numeric matching with 1% tolerance
- ONLY the content of /app/answer.txt is evaluated
- No partial credit -- answer is either correct (1.0) or wrong (0.0)

## Format by Question Type

| Question asks for | Format | Example |
|-------------------|--------|---------|
| "rounded to nearest hundredths" | 2 decimal places | 12.34 |
| "rounded to nearest tenths" | 1 decimal place | 12.3 |
| "rounded to nearest thousandth" | 3 decimal places | 12.345 |
| "as a percent value (12.34%)" | Number with % | 12.34% |
| "in billions" | Number in billions | 8.124 |
| "in millions of dollars" | Number in millions | 1234.56 |
| Multi-part with brackets | Bracketed, comma-separated | [8.124, 12.852] |
| Date | Written date | March 3, 1977 |
| Count/integer | Whole number | 18 |

## Common Mistakes
- Writing explanation text in answer.txt (should be ONLY the value)
- Including "$" when not asked for
- Rounding to wrong decimal places
- Forgetting "%" when question specifies percent format
- Using wrong separator in multi-part answers (use comma + space)
- Writing "approximately" or "about" -- give exact computed value
