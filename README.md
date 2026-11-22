# Girls' access to government schooling in Khyber Pakhtunkhwa (2023-24 and 2024-25)

A data pipeline, PostgreSQL warehouse, analysis and Power BI dashboard on gender parity in government school enrolment across KP districts. It is built from the official Annual School Census reports of the KP Elementary & Secondary Education Department. The focus is middle school (classes 6-8).

## Questions
1. How does girls' enrolment compare with boys' across districts, by school level?
2. How do girls' and boys' middle schools compare by district?
3. Where does the gap open up, and do school counts explain it?

## Data
- **2024-25:** Schools Statistical Report 2024-25 (https://kpese.gov.pk/wp-content/uploads/2026/07/Annual-Schools-Statistical-Report-2024-25.pdf).
- **2023-24:** Annual School Census 2023-24, listed at https://kpese.gov.pk/category/annual-school-census/.
- **Scope:** government schools only. 41 comparison units (28 settled districts and 13 merged-area units). South Waziristan Lower and Upper are combined in 2024-25 because the 2023-24 report reports one South Waziristan.
- The PDFs are not stored in this repository. Save them as `data/raw/asr_2024_25.pdf` and `data/raw/asr_2023_24.pdf`.

## Pipeline
1. **Extract** tables from the PDFs with `pdfplumber`: published GPI, schools by level and gender, class-wise enrolment for boys and girls, and class 5-to-6 transition rates (`extract_*.py`, `transition.py`, `district_names.py`).
2. **Clean and validate** (see below). Districts are mapped to standard names in `district_names.py`.
3. **Load** into PostgreSQL (`kp_education`) as a star schema: `dim_district`, `dim_year`, `fact_enrolment`, `fact_schools`, `fact_transition`, `fact_gpi` (`load_*.py`, `flags.py`).
4. **Analyse:** the view `v_unit_year` (`create_views.py`) joins the tables by comparison unit and year. `analysis.py` computes correlations and a small regression, and `charts.py` draws the figures.
5. **Dashboard:** Power BI report in `dashboard/` (`kp_dashboard.pbix`, a PDF export and screenshots).

## Validation
- **Totals reconcile with each report's own totals** in both years:
  - Schools: 34,784 (2024-25) and 34,633 (2023-24; the settled and merged tables sum to their Grand Total rows at every level).
  - Enrolment: 2024-25 is 3,308,058 boys and 2,631,627 girls. 2023-24 is 3,255,179 boys and 2,586,275 girls.
  - Every enrolment row also passes its own class-group subtotals.
- **Transition rates** are recomputed from the counts, as (class-6 enrolment minus repeaters) divided by the previous year's class-5 enrolment. They match the published rates in every unit (2023-24 rates are published as whole percentages).
- **Cross-year check:** the class-5 counts in the 2024-25 transition table equal the class-5 enrolment in the 2023-24 report for every unit.
- **Published GPIs are not comparable across years** (their definitions differ), so GPI is recomputed the same way for both years as girls enrolled per boy enrolled, from the counts.
- **Repair:** Malakand's name cell was blank in the 2024-25 enrolment tables. The nameless row was assigned to it because its totals matched the gap to the report's Grand Totals exactly.

## Data-quality findings
- **SD Bhetani, 2023-24:** only 6 girls in class 5, but 61 in class 6 the next year, so the published girls' transition rate is 1,017%. It is flagged `low_base` (fewer than 100 students in class 5) and excluded from the transition statistics.
- **Rates above 100%** (`above_100` flag): Haripur and Chitral Upper (girls) in both years, SD Bhetani in 2023-24, and SD Dara Adam Khel (boys) in 2024-25. These suggest inflow from outside government schools. They are kept and flagged, not deleted.
- Source PDFs have font glitches, blank cells that vanish from the extracted text, and changing district names. The grid-based extraction and the reconciliation checks above are there to catch these.

## Findings (41 units, medians)
| | 2023-24 | 2024-25 |
|---|---|---|
| Girls per boy enrolled, primary (classes 1-5) | 0.83 | 0.80 |
| Girls per boy enrolled, middle (6-8) | 0.56 | 0.58 |
| Girls per boy enrolled, high (9-10) | 0.44 | 0.45 |
| Girls' middle schools per boys' middle school | 0.86 | 0.83 |
| Girls' class 5-to-6 transition, settled / merged | 83% / 75% | 72% / 58% |

- **Parity drops most between primary and middle school,** and this is the same in both years.
- **Girls' transition from class 5 to 6 fell** between the two years (median 78.5% to 66.0%), with a larger fall in merged units.
- **Lowest middle-school parity (2024-25):** Kohistan Lower (0.08), Kohistan Upper (0.12), Kolai Palas (0.19), Torghar (0.21), Battagram (0.26). Abbottabad (1.04), Haripur (1.02) and Chitral Upper (1.01) are at or above parity.
- **School counts explain only part of it.** The rank correlation between girls' middle schools per boys' school and girls-per-boy enrolment is 0.40 in 2023-24 (95% bootstrap interval 0.10 to 0.65) and 0.44 in 2024-25 (0.09 to 0.69). Merged areas have about as many girls' schools per boys' school as settled districts (0.86 against 0.81 in 2024-25) but far fewer girls enrolled (median 0.40 against 0.66). A regression with the school ratio and a merged-area flag has R-squared 0.35 in both years.

## Limitations
- Government schools only: no private schools or madrasas.
- Enrolment in classes 6-8 is not the same as enrolment in middle schools, because some high schools teach those classes.
- Ratios are of enrolment counts, not adjusted for child population, and each unit counts equally whatever its size. Small units give noisy ratios.
- School counts say nothing about school size, distance or whether a school is functioning.
- The transition rate is not a dropout rate: it ignores movement between school types and into the system.
- Only two adjacent years, covering mostly the same units, so this shows association, not trend or cause.
- The `.pbix` file has the data embedded. It can be viewed without the database, but cannot be refreshed without a local PostgreSQL copy.
- The 2021-22 report was reviewed but not loaded: it uses older district names (Dir Bala/Payan, combined Chitral and Kohistan) and appears to define its published GPI differently.

## Run it yourself
```
python -m venv .venv
.venv\Scripts\activate
pip install pandas pdfplumber openpyxl matplotlib sqlalchemy psycopg2-binary
```
1. Create a PostgreSQL database called `kp_education`. The scripts ask for the password when they run, and no password is stored in the code.
2. Save the PDFs as described under Data.
3. Run, in order: `extract_*.py` and `transition.py` (2024-25), `extract_*_2023_24.py`, `load_dims.py`, `load_facts.py`, `load_2023_24.py`, `load_schools_2023_24.py`, `flags.py`, `create_views.py`, `analysis.py`, `charts.py`.