import pandas as pd
from sqlalchemy import text
from db_utils import get_engine

YEAR = "2023-24"
DIR = r"D:\edu-project\data\processed"
CLASS_COLS = ["nursery", "prep"] + [f"class_{n}" for n in range(1, 13)] + ["grand_total"]
COUNT_COLS = ["c5_boys", "c5_girls", "c5_total", "c6_boys", "c6_girls", "c6_total",
              "rep_boys", "rep_girls", "rep_total"]
RATE_COLS = ["rate_boys", "rate_girls", "rate_total"]

engine = get_engine()

with engine.begin() as conn:
    # 1. The comparison unit: lets us compare years where district boundaries differ
    conn.execute(text("ALTER TABLE dim_district ADD COLUMN IF NOT EXISTS comparison_unit TEXT"))
    conn.execute(text("""
        UPDATE dim_district
        SET comparison_unit = CASE WHEN district_name LIKE 'South Waziristan%'
                                   THEN 'South Waziristan' ELSE district_name END
        WHERE comparison_unit IS NULL
    """))
    conn.execute(text("""
        INSERT INTO dim_district (district_name, area, comparison_unit)
        VALUES ('South Waziristan', 'Merged', 'South Waziristan')
        ON CONFLICT (district_name) DO NOTHING
    """))
    conn.execute(text("""
        INSERT INTO dim_year (report_year, start_year) VALUES (:y, 2023)
        ON CONFLICT (report_year) DO NOTHING
    """), {"y": YEAR})

    # 2. A flag for unreliable transition rates
    conn.execute(text("ALTER TABLE fact_transition ADD COLUMN IF NOT EXISTS low_base BOOLEAN"))

    ids = pd.read_sql(text("SELECT district_id, district_name FROM dim_district"), conn)
    id_map = dict(zip(ids["district_name"], ids["district_id"]))

    def prepare(df, columns):
        df = df.copy()
        df["district_id"] = df["district"].map(id_map)
        assert df["district_id"].notna().all(), "a district name did not match dim_district"
        df["report_year"] = YEAR
        return df[["district_id", "report_year"] + columns]

    def load(table, df):
        conn.execute(text(f"DELETE FROM {table} WHERE report_year = :y"), {"y": YEAR})
        df.to_sql(table, conn, if_exists="append", index=False)
        print(f"loaded {len(df)} rows into {table} for {YEAR}")

    enrol = pd.read_csv(DIR + r"\enrolment_2023_24.csv")
    load("fact_enrolment", prepare(enrol, ["sex"] + CLASS_COLS))

    trans = pd.read_csv(DIR + r"\transition_2023_24.csv")
    for c in COUNT_COLS:
        trans[c] = trans[c].astype(int)
    load("fact_transition", prepare(trans, COUNT_COLS + RATE_COLS))

    # 3. Flag unreliable rates for BOTH years: base under 100 students, or a rate above 100%
    conn.execute(text("""
        UPDATE fact_transition
        SET low_base = (LEAST(c5_boys, c5_girls) < 100
                        OR GREATEST(rate_boys, rate_girls) > 100)
    """))

# ---- checks, answered by the database ----
with engine.connect() as conn:
    print("\nRows per year:")
    for table in ["fact_enrolment", "fact_transition"]:
        print(" ", table, conn.execute(text(
            f"SELECT report_year, COUNT(*) FROM {table} GROUP BY report_year ORDER BY report_year")).all())

    print("\nEnrolment totals by year and sex:")
    print(conn.execute(text("""
        SELECT report_year, sex, SUM(grand_total)
        FROM fact_enrolment GROUP BY report_year, sex ORDER BY report_year, sex
    """)).all())

    print("\nUnits flagged as unreliable transition rates:")
    for row in conn.execute(text("""
        SELECT d.district_name, t.report_year, t.c5_boys, t.c5_girls, t.rate_boys, t.rate_girls
        FROM fact_transition t JOIN dim_district d USING (district_id)
        WHERE t.low_base ORDER BY t.report_year, d.district_name
    """)).all():
        print(" ", row)