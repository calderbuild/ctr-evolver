# Answer Formatting Rules

## CRITICAL: Write to /app/answer.txt
```bash
echo "YOUR_ANSWER" > /app/answer.txt
```
Write ONLY the final value. No text, no explanation, no dollar signs, no unit words.

## Scoring Logic (How Your Answer is Evaluated)
- Fuzzy numeric matching with **1% tolerance** on base numbers
- **Base number comparison**: "543 million" has base=543. Your answer "543" matches. But "543000000" does NOT match (different base).
- **Year filtering**: Numbers 1900-2100 in your answer are IGNORED unless the expected answer is itself a year. Don't output stray year numbers.
- **Multi-value**: ALL expected numbers must appear in your answer. Missing even one = score 0.
- **Text overlap**: For answers like "March 1977", both the text ("March") and number (1977) must match.
- No partial credit -- 1.0 or 0.0.

## Output Rules
1. Write ONLY the numeric answer -- no units ("million", "billion"), no "$", no explanation
2. If question says "in billions", output just the number in billions (e.g., "8.124" not "8.124 billion")
3. Do NOT output extra numbers in answer.txt -- they can cause false mismatches
4. Round ONLY at the final step, never intermediate steps

## Format by Question Type

| Question asks for | Format | Example |
|-------------------|--------|---------|
| "rounded to nearest hundredths" | 2 decimal places | 12.34 |
| "rounded to nearest tenths" | 1 decimal place | 12.3 |
| "rounded to nearest thousandth" | 3 decimal places | 12.345 |
| "as a percent value (12.34%)" | Number with % | 12.34% |
| "in billions" | Just the number | 8.124 |
| "in millions of dollars" | Just the number | 1234.56 |
| Multi-part with brackets | Bracketed list | [8.124, 12.852] |
| List of large numbers | Keep thousands commas | [374,443, 381,327, 401,845] |
| Date | Written date | March 3, 1977 |
| Count/integer | Whole number | 18 |
| Country names | Comma-separated list | France, Netherlands, Switzerland |

## List/Array Answers
- Use square brackets: [val1, val2, val3]
- Separate with comma + space
- Keep thousands-separator commas within numbers: [374,443, 381,327]
- Order matters: follow the order specified in the question
- If question says "from 1969 to 1980 inclusive", include ALL years (12 values)
- Double-check: count of values matches expected range

## Common Mistakes
- Including unit words ("million", "billion") -- just write the number
- Including "$" -- never write dollar signs
- Writing explanation text -- answer.txt must contain ONLY the value
- Rounding too early -- round ONLY at the final step
- Forgetting "%" when question says "percent value"
- Outputting stray numbers (dates, page numbers) that confuse the matcher
- Wrong decimal precision: "hundredths" = exactly 2 decimal places
- Dropping values from a list -- verify count before writing
