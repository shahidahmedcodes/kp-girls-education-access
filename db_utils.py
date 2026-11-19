from getpass import getpass
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


def get_engine():
    password = getpass("PostgreSQL password: ")
    url = URL.create(
        "postgresql+psycopg2",
        username="postgres",
        password=password,
        host="localhost",
        port=5432,
        database="kp_education",
    )
    return create_engine(url)