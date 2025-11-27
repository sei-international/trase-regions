import os

import psycopg2
import pandas.io.sql as sqlio

from helpers.yaml import parse_yaml


def run_sql_return_df(query):
    secrets_path = os.path.join(os.path.dirname(__file__), "../secrets.yml")
    secrets = parse_yaml(secrets_path)
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
