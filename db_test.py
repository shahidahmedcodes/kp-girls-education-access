from getpass import getpass
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

password = getpass("PostgreSQL password: ")

url = URL.create(
    "postgresql+psycopg2",
    username="postgres",
    password=password,
    host="localhost",
    port=5432,
    database="kp_education",
)
engine = create_engine(url)

with engine.connect() as conn:
    print(conn.execute(text("select version()")).scalar())
    print("Connected to:", conn.execute(text("select current_database()")).scalar())