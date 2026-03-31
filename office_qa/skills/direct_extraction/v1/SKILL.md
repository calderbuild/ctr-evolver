# direct_extraction

## Strategy Description
Locate and extract exact numerical values directly from Treasury Bulletin tables. Best for questions asking for a single reported value from a specific document and time period.

## Applicable Question Types
- "What was the total X reported in [month/year]?"
- "What is the value of X as of [date]?"
- Single-value lookup questions

## Core Techniques
1. Identify the exact bulletin file from the date reference (treasury_bulletin_YYYY_MM.txt)
2. Search for the table containing the target metric using grep
3. Read the full table including all header rows to understand column structure
4. Extract the value from the correct row and column intersection
5. Pay attention to units in table headers (millions, billions, thousands)

## Examples
Question: "What was the total federal expenditure reported in January 1941?"
Reasoning: Open treasury_bulletin_1941_01.txt -> find expenditure table -> read the total row -> note units
Answer: The value directly from the table, with correct units

## Prompt Template
When answering, follow this exact sequence:
1. Which file(s) should contain this data?
2. What table am I looking for? (grep for key terms)
3. What are the column headers? (read carefully, may span multiple rows)
4. What row contains my target?
5. What is the exact value? What units?
6. Write the answer in the format the question requests.
