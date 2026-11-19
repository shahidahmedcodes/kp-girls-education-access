import pandas as pd
from sqlalchemy import text
from db_utils import get_engine

YEAR = "2023-24"
SCHOOL_COLS = [
    "boys_primary", "boys_middle", "boys_high", "boys_higher_sec", "boys_total",
    "girls_primary", "girls_middle", "girls_high", "girls_higher_sec", "girls_total",
    "grand_total",
]

engine = get_engine()
df = pd.read_csv(r"D:\edu-project\data\processed\schools_2023_24.csv")

with engine.begin() as conn:
    ids = pd.read_sql(text("SELECT district_id, district_name FROM dim_district"), conn)
    id_map = dict(zip(ids["district_name"], ids["district_id"]))
    df["district_id"] = df["district"].map(id_map)
    assert df["district_id"].notna().all(), "a district name did not match dim_district"
    df["report_year"] = YEAR
    out = df[["district_id", "report_year"] + SCHOOL_COLS]
    conn.execute(text("DELETE FROM fact_schools WHERE report_year = :y"), {"y": YEAR})
    out.to_sql("fact_schools", conn, if_exists="append", index=False)
    print("loaded", len(out), "rows into fact_schools for", YEAR)

with engine.connect() as conn:
    print(conn.execute(text("""
        SELECT report_year, COUNT(*), SUM(boys_total), SUM(girls_total), SUM(grand_total)
        FROM fact_schools GROUP BY report_year ORDER BY report_year
    """)).all())