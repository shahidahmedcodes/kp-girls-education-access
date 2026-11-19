import pandas as pd
from sqlalchemy import text
from db_utils import get_engine

GPI_PATH = r"D:\edu-project\data\processed\gpi_2024_25_clean.csv"

engine = get_engine()
districts = pd.read_csv(GPI_PATH)[["district", "area"]].drop_duplicates()

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS dim_district (
            district_id SERIAL PRIMARY KEY,
            district_name TEXT NOT NULL UNIQUE,
            area TEXT NOT NULL
        )
    """))
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS dim_year (
            report_year TEXT PRIMARY KEY,
            start_year INTEGER NOT NULL
        )
    """))
    for row in districts.itertuples(index=False):
        conn.execute(
            text("""
                INSERT INTO dim_district (district_name, area)
                VALUES (:name, :area)
                ON CONFLICT (district_name) DO NOTHING
            """),
            {"name": row.district, "area": row.area},
        )
    conn.execute(text("""
        INSERT INTO dim_year (report_year, start_year)
        VALUES ('2024-25', 2024)
        ON CONFLICT (report_year) DO NOTHING
    """))

with engine.connect() as conn:
    print("districts in dim_district:", conn.execute(text("SELECT COUNT(*) FROM dim_district")).scalar())
    print(conn.execute(text("SELECT area, COUNT(*) FROM dim_district GROUP BY area ORDER BY area")).all())