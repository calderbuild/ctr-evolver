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
| List of large numbers | Keep thousands commas | [374,443, 381,327, 401,845] |
| Date | Written date | March 3, 1977 |
| Count/integer | Whole number | 18 |
| Country names | Comma-separated list | France, Netherlands, Switzerland |

## List/Array Answers
When the question asks for multiple values (e.g., "List the values from X to Y"):
- Use square brackets: [val1, val2, val3]
- Separate with comma + space
- Keep thousands-separator commas within numbers: [374,443, 381,327]
- Order matters: follow the order specified in the question (chronological, ascending, etc.)
- If question says "from 1969 to 1980 inclusive", include ALL years in that range

## Common Mistakes
- Writing explanation text in answer.txt (should be ONLY the value)
- Including "$" when not asked for
- Rounding to wrong decimal places
- Forgetting "%" when question specifies percent format
- Using wrong separator in multi-part answers (use comma + space)
- Writing "approximately" or "about" -- give exact computed value
- Dropping values from a list -- double-check count matches expected range
- Wrong decimal precision: if question says "hundredths", use exactly 2 decimal places
