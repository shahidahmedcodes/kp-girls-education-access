from sqlalchemy import text
from db_utils import get_engine

engine = get_engine()

with engine.begin() as conn:
    conn.execute(text("ALTER TABLE fact_transition ADD COLUMN IF NOT EXISTS above_100 BOOLEAN"))
    conn.execute(text("""
        UPDATE fact_transition SET
            low_base = (LEAST(c5_boys, c5_girls) < 100),
            above_100 = (GREATEST(rate_boys, rate_girls) > 100)
    """))

with engine.connect() as conn:
    print("year, low_base rows, above_100 rows, total rows:")
    print(conn.execute(text("""
        SELECT report_year, SUM(low_base::int), SUM(above_100::int), COUNT(*)
        FROM fact_transition GROUP BY report_year ORDER BY report_year
    """)).all())