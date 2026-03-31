# temporal_reasoning

## Strategy Description
Handle questions that require understanding time periods, historical events, fiscal vs calendar years, and finding the correct bulletin for a given date. Critical for questions with indirect time references.

## Applicable Question Types
- "1 year before the start of WW2" (requires knowing WW2 dates)
- "fiscal year 1953" (requires knowing fiscal year boundaries)
- "the most recent revised value" (requires checking multiple bulletins)
- Any question with indirect date references

## Core Techniques
1. Resolve indirect time references to exact dates:
   - WW2 start: September 1939 (Europe) / December 1941 (US entry)
   - Korean War: 1950-1953
   - Fiscal year pre-1977: July-June (FY1953 = Jul 1952 - Jun 1953)
   - Fiscal year post-1977: October-September
2. Find the RIGHT bulletin for a time period:
   - Monthly data for year X appears in bulletins from that year
   - Annual summaries often in January/February of the following year
3. Check for revised values -- later bulletins may update earlier figures
4. "Calendar year" means January-December; "fiscal year" has different boundaries

## Examples
Question: "What was the total intergovernmental transfers 1 year before the start of WW2?"
Reasoning:
- WW2 started September 1939 for most contexts
- 1 year before = 1938
- Look for 1938 annual data in treasury_bulletin_1939_01.txt or nearby
- The question asks for a total, so find the annual summary table

## Prompt Template
1. Parse the time reference: what exact year/month is being asked about?
2. If ambiguous (WW2, "before X"), state my interpretation explicitly
3. Which bulletin file(s) would contain this data?
4. Is there a calendar vs fiscal year distinction that matters?
5. Extract the value and verify the time period matches
