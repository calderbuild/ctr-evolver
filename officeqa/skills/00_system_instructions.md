# System Instructions -- READ THIS FIRST

You MUST write your final answer to /app/answer.txt. If you don't write this file, you score 0.

Be efficient. Do not over-explain. Focus on finding data and computing the answer.

## Corpus

697 Treasury Bulletin text files at /app/corpus/ named treasury_bulletin_YYYY_MM.txt.
File index: /app/corpus/index.txt

## Workflow

1. PARSE: What data? What years/months? What calculation? What output format (decimals, %, brackets)?

2. SEARCH: Find the right file(s).
   - grep -rl "keyword" /app/corpus/ to find files containing a term
   - Data for calendar year X often appears in bulletins from Jan-Mar of year X+1
   - Fiscal year: before 1977 = Jul-Jun, after 1977 = Oct-Sep

3. EXTRACT: Read the file. Tables use | separators. CRITICAL:
   - Check ALL header rows for units (millions, billions, thousands)
   - (123) means NEGATIVE 123
   - A dash (-) means zero
   - Split rows by | and count columns carefully to get the right value

4. CALCULATE: Use python3 for ALL math. Never mental arithmetic.
   python3 -c "result = ...; print(round(result, N))"
   For complex formulas, read skills/formulas.py and run: python3 skills/formulas.py <function> <args>

5. WRITE: echo "ANSWER_ONLY" > /app/answer.txt
   - Only the final value. No explanation. No units unless the question specifies them.
   - Percent: "12.34%" | Multi-part: "[8.124, 12.852]" | Date: "March 3, 1977"

## Common Errors to Avoid
- Wrong file: check adjacent months/years if first search fails
- Wrong column: count | separators, don't eyeball alignment
- Rounding too early: round only at the final step
- "Absolute" means use abs()
- Forgetting to write /app/answer.txt
