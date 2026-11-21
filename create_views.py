from sqlalchemy import text
from db_utils import get_engine

VIEW_SQL = """
CREATE OR REPLACE VIEW v_unit_year AS
WITH units AS (
    SELECT comparison_unit AS unit, MIN(area) AS area
    FROM dim_district GROUP BY comparison_unit
),
enrol AS (
    SELECT d.comparison_unit AS unit, e.report_year,
        SUM(e.class_1+e.class_2+e.class_3+e.class_4+e.class_5) FILTER (WHERE e.sex = 'boys')  AS enrol_boys_primary,
        SUM(e.class_1+e.class_2+e.class_3+e.class_4+e.class_5) FILTER (WHERE e.sex = 'girls') AS enrol_girls_primary,
        SUM(e.class_6+e.class_7+e.class_8) FILTER (WHERE e.sex = 'boys')  AS enrol_boys_middle,
        SUM(e.class_6+e.class_7+e.class_8) FILTER (WHERE e.sex = 'girls') AS enrol_girls_middle,
        SUM(e.class_9+e.class_10) FILTER (WHERE e.sex = 'boys')  AS enrol_boys_high,
        SUM(e.class_9+e.class_10) FILTER (WHERE e.sex = 'girls') AS enrol_girls_high
    FROM fact_enrolment e JOIN dim_district d USING (district_id)
    GROUP BY d.comparison_unit, e.report_year
),
sch AS (
    SELECT d.comparison_unit AS unit, s.report_year,
        SUM(s.boys_middle) AS sch_boys_middle, SUM(s.girls_middle) AS sch_girls_middle
    FROM fact_schools s JOIN dim_district d USING (district_id)
    GROUP BY d.comparison_unit, s.report_year
),
tr AS (
    SELECT d.comparison_unit AS unit, t.report_year,
        SUM(t.c5_boys) AS c5_boys, SUM(t.c5_girls) AS c5_girls,
        ROUND((SUM(t.c6_boys) - SUM(t.rep_boys))::numeric / NULLIF(SUM(t.c5_boys), 0) * 100, 1)   AS trans_boys,
        ROUND((SUM(t.c6_girls) - SUM(t.rep_girls))::numeric / NULLIF(SUM(t.c5_girls), 0) * 100, 1) AS trans_girls
    FROM fact_transition t JOIN dim_district d USING (district_id)
    GROUP BY d.comparison_unit, t.report_year
)
SELECT u.unit, u.area, en.report_year,
    en.enrol_boys_primary, en.enrol_girls_primary,
    en.enrol_boys_middle,  en.enrol_girls_middle,
    en.enrol_boys_high,    en.enrol_girls_high,
    ROUND(en.enrol_girls_primary::numeric / NULLIF(en.enrol_boys_primary, 0), 3) AS gpb_primary,
    ROUND(en.enrol_girls_middle::numeric  / NULLIF(en.enrol_boys_middle, 0), 3)  AS gpb_middle,
    ROUND(en.enrol_girls_high::numeric    / NULLIF(en.enrol_boys_high, 0), 3)    AS gpb_high,
    sc.sch_boys_middle, sc.sch_girls_middle,
    ROUND(sc.sch_girls_middle::numeric / NULLIF(sc.sch_boys_middle, 0), 3) AS schools_gpb_middle,
    tr.c5_boys, tr.c5_girls, tr.trans_boys, tr.trans_girls,
    (LEAST(tr.c5_boys, tr.c5_girls) < 100) AS low_base,
    (GREATEST(tr.trans_boys, tr.trans_girls) > 100) AS above_100
FROM units u
JOIN enrol en ON en.unit = u.unit
JOIN sch sc   ON sc.unit = u.unit AND sc.report_year = en.report_year
JOIN tr       ON tr.unit = u.unit AND tr.report_year = en.report_year
"""

engine = get_engine()
with engine.begin() as conn:
    conn.execute(text(VIEW_SQL))

with engine.connect() as conn:
    print("units, low_base and above_100 flags per year:")
    print(conn.execute(text("""
        SELECT report_year, COUNT(*), SUM(low_base::int), SUM(above_100::int)
        FROM v_unit_year GROUP BY report_year ORDER BY report_year
    """)).all())

    print("\nMedians by year (girls per boy, and transition rates in %):")
    for row in conn.execute(text("""
        SELECT report_year,
            ROUND(CAST(percentile_cont(0.5) WITHIN GROUP (ORDER BY gpb_primary) AS numeric), 2) AS primary,
            ROUND(CAST(percentile_cont(0.5) WITHIN GROUP (ORDER BY gpb_middle) AS numeric), 2) AS middle,
            ROUND(CAST(percentile_cont(0.5) WITHIN GROUP (ORDER BY gpb_high) AS numeric), 2) AS high,
            ROUND(CAST(percentile_cont(0.5) WITHIN GROUP (ORDER BY schools_gpb_middle) AS numeric), 2) AS mid_schools,
            ROUND(CAST(percentile_cont(0.5) WITHIN GROUP (ORDER BY trans_girls) AS numeric), 1) AS trans_girls
        FROM v_unit_year GROUP BY report_year ORDER BY report_year
    """)).all():
        print(" ", row)

    print("\nLowest middle-school girls-per-boy in 2024-25:")
    for row in conn.execute(text("""
        SELECT unit, gpb_middle, schools_gpb_middle, trans_girls
        FROM v_unit_year WHERE report_year = '2024-25'
        ORDER BY gpb_middle LIMIT 5
    """)).all():
        print(" ", row)