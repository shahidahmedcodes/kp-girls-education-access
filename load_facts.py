import pandas as pd
from sqlalchemy import text
from db_utils import get_engine

YEAR = "2024-25"
DIR = r"D:\edu-project\data\processed"

CLASS_COLS = ["nursery", "prep"] + [f"class_{n}" for n in range(1, 13)] + ["grand_total"]
SCHOOL_COLS = [
    "boys_primary", "boys_middle", "boys_high", "boys_higher_sec", "boys_total",
    "girls_primary", "girls_middle", "girls_high", "girls_higher_sec", "girls_total",
    "grand_total",
]
COUNT_COLS = ["c5_boys", "c5_girls", "c5_total", "c6_boys", "c6_girls", "c6_total",
              "rep_boys", "rep_girls", "rep_total"]
RATE_COLS = ["rate_boys", "rate_girls", "rate_total"]
GPI_RENAME = {
    "prim_boys": "ger_primary_boys", "prim_girls": "ger_primary_girls", "prim_gpi": "gpi_primary",
    "sec_boys": "ger_secondary_boys", "sec_girls": "ger_secondary_girls", "sec_gpi": "gpi_secondary",
}

KEYS = """
    district_id INTEGER NOT NULL REFERENCES dim_district(district_id),
    report_year TEXT NOT NULL REFERENCES dim_year(report_year),
"""


def ints(cols):
    return ", ".join(f"{c} INTEGER" for c in cols)


DDL = {
    "fact_gpi": f"""CREATE TABLE IF NOT EXISTS fact_gpi ({KEYS}
        ger_primary_boys NUMERIC(6,1), ger_primary_girls NUMERIC(6,1), gpi_primary NUMERIC(5,2),
        ger_secondary_boys NUMERIC(6,1), ger_secondary_girls NUMERIC(6,1), gpi_secondary NUMERIC(5,2),
        PRIMARY KEY (district_id, report_year))""",
    "fact_schools": f"""CREATE TABLE IF NOT EXISTS fact_schools ({KEYS}
        {ints(SCHOOL_COLS)}, PRIMARY KEY (district_id, report_year))""",
    "fact_enrolment": f"""CREATE TABLE IF NOT EXISTS fact_enrolment ({KEYS}
        sex TEXT NOT NULL CHECK (sex IN ('boys','girls')),
        {ints(CLASS_COLS)}, PRIMARY KEY (district_id, report_year, sex))""",
    "fact_transition": f"""CREATE TABLE IF NOT EXISTS fact_transition ({KEYS}
        {ints(COUNT_COLS)}, rate_boys NUMERIC(6,2), rate_girls NUMERIC(6,2), rate_total NUMERIC(6,2),
        PRIMARY KEY (district_id, report_year))""",
}

engine = get_engine()

with engine.begin() as conn:
    ids = pd.read_sql(text("SELECT district_id, district_name FROM dim_district"), conn)
    id_map = dict(zip(ids["district_name"], ids["district_id"]))

    for ddl in DDL.values():
        conn.execute(text(ddl))

    def prepare(df, columns):
        df = df.copy()
        df["district_id"] = df["district"].map(id_map)
        assert df["district_id"].notna().all(), "a district name did not match dim_district"
        df["report_year"] = YEAR
        return df[["district_id", "report_year"] + columns]

    def load(table, df):
        conn.execute(text(f"DELETE FROM {table} WHERE report_year = :y"), {"y": YEAR})
        df.to_sql(table, conn, if_exists="append", index=False)
        print(f"loaded {len(df)} rows into {table}")

    gpi = pd.read_csv(DIR + r"\gpi_2024_25_clean.csv").rename(columns=GPI_RENAME)
    load("fact_gpi", prepare(gpi, list(GPI_RENAME.values())))

    schools = pd.read_csv(DIR + r"\schools_2024_25.csv")
    load("fact_schools", prepare(schools, SCHOOL_COLS))

    enrol = pd.read_csv(DIR + r"\enrolment_2024_25.csv")
    load("fact_enrolment", prepare(enrol, ["sex"] + CLASS_COLS))

    trans = pd.read_csv(DIR + r"\transition_2024_25.csv")
    load("fact_transition", prepare(trans, COUNT_COLS + RATE_COLS))

# ---- checks, this time answered by the database itself ----
with engine.connect() as conn:
    print("\nSchools, all districts (report says 34784):",
          conn.execute(text("SELECT SUM(grand_total) FROM fact_schools")).scalar())
    print("Enrolment totals by sex (report says boys 3308058, girls 2631627):",
          conn.execute(text("SELECT sex, SUM(grand_total) FROM fact_enrolment GROUP BY sex ORDER BY sex")).all())
    print("\nLowest girls-per-boy enrolment in classes 6-8, from SQL:")
    rows = conn.execute(text("""
        SELECT d.district_name,
               ROUND(CAST(g.class_6 + g.class_7 + g.class_8 AS NUMERIC)
                     / (b.class_6 + b.class_7 + b.class_8), 2) AS girls_per_boy
        FROM fact_enrolment g
        JOIN fact_enrolment b ON b.district_id = g.district_id
             AND b.report_year = g.report_year AND b.sex = 'boys'
        JOIN dim_district d ON d.district_id = g.district_id
        WHERE g.sex = 'girls' AND g.report_year = :y
        ORDER BY girls_per_boy LIMIT 5
    """), {"y": YEAR}).all()
    for name, ratio in rows:
        print(f"  {name}: {ratio}")