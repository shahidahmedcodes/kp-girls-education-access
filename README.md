# Girls' access to government schooling in Khyber Pakhtunkhwa (2024-25)

A small data pipeline and analysis of gender parity in government school enrolment across KP districts, built from the official Annual Schools Statistical Report 2024-25 (KP Elementary & Secondary Education Department).

## Questions
1. How does girls' enrolment compare with boys' across districts, by level (primary, middle, high, higher secondary)?
2. How do girls' and boys' middle schools compare by district?
3. Where does the gap open up, and do school counts explain it?

## Data
- Source: *Schools Statistical Report 2024-25*, KP E&SE Department (https://kpese.gov.pk/wp-content/uploads/2026/07/Annual-Schools-Statistical-Report-2024-25.pdf).
- Scope: government schools only; 42 districts (28 settled, 14 merged areas).
- The PDF is not stored in this repository.

## Pipeline
1. `extract_gpi.py` and `clean_gpi.py`: extract and clean the published Gender Parity Index table.
2. `extract_tables.py`: extract schools by level and gender, and class-wise enrolment for boys and girls.
3. `transition.py`: extract the class 5-to-6 transition rates.
4. `levels.py` and `crosscheck.py`: derive girls-per-boy ratios by level and compare them with the published GPI.

## Validation
- Schools: district counts sum to the report's 34,784; levels add up to totals in every district.
- Enrolment: district sums match the report's grand totals (3,308,058 boys; 2,631,627 girls); classes add up to row totals.
- Transition rates: recomputed from the counts and match the published rates in every district; sums match the report's totals.
- Our classes 6-8 girls-per-boy ratio correlates 0.96 with the report's published secondary GPI.
- Repair: Malakand's name cell was blank in the enrolment tables. The nameless row was assigned to it because its total matched the gap to the report's grand total exactly (81,863 boys; 78,123 girls).

## Early observations (descriptive, one year, not causal)
- Median girls-per-boy ratio across districts: 0.80 in primary, 0.57 in middle, 0.48 in high, 0.47 in higher secondary.
- Median class 5-to-6 transition: about 76% for boys and 65% for girls; girls' rate is lower in 35 of 42 districts.
- Districts with relatively more girls' middle schools tend to have more girls enrolled (correlation 0.44), but merged districts have similar school ratios to settled ones and much lower enrolment ratios.

## Limitations
- Government schools only (no private schools or madrasas).
- Classes 6-8 are also taught in some high schools, so enrolment in those classes is not the same as enrolment in middle schools.
- The transition rate is not a pure dropout rate: it ignores movement to private schools and from outside the system.
- Small districts give noisy ratios.

## Planned
- Add 2021-22 and 2018-19 reports for trends.
- Load into PostgreSQL with a star schema; add a dashboard.
- Add population denominators (girls 10-14) to measure schools per child.

## Run
```
python -m venv .venv
.venv\Scripts\activate
pip install pandas pdfplumber openpyxl matplotlib
```
Download the PDF to `data/raw/asr_2024_25.pdf`, then run the scripts in the order above.