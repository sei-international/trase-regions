import psycopg2
import pandas.io.sql as sqlio

from helpers.yaml import parse_yaml


def run_sql_return_df(query):
    secrets = parse_yaml("extract_trase_regions/secrets.yml")
    USER = secrets["user"]
    PASSWORD = secrets["password"]
    HOST = secrets["host"]
    PORT = secrets["port"]
    DB_NAME = secrets["db_name"]
    with psycopg2.connect(
        dsn=f"postgresql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}"
    ) as conn:
        # with conn.cursor() as cur:
        #     cur.execute(query)
        #     result = cur.fetchall()
        #     return result
        return sqlio.read_sql_query(query, conn)
        conn.close()
