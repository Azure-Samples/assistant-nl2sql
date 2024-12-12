import pandas as pd
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
import chardet

load_dotenv(override=True)


def _config():
    return {
        "db_params": {
            "host": os.getenv("AZURE_POSTGRES_SERVER") + ".postgres.database.azure.com",
            "port": 5432,
            "dbname": os.getenv("AZURE_POSTGRES_DATABASE"),
            "user": os.getenv("AZURE_POSTGRES_USER"),
            "password": os.getenv("AZURE_POSTGRES_PASSWORD"),
        }
    }


def create_database(database_name):
    conn = psycopg2.connect(get_pg_connection("postgres"))
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE {database_name}")
    cursor.close()
    conn.close()
    conn.close()


def get_pg_connection(database_name="postgres"):
    return f"postgresql://{_config()['db_params']['user']}:{_config()['db_params']['password']}@{_config()['db_params']['host']}:{_config()['db_params']['port']}/{database_name if database_name else _config()['db_params']['dbname']}"


def import_csv_to_pgsql(csv_file_path, database_name, table_name):

    with open(csv_file_path, 'rb') as f:
        result = chardet.detect(f.read())
    
    # Read CSV file
    df = pd.read_csv(csv_file_path, encoding=result['encoding'])

    # Create SQLAlchemy engine
    engine = create_engine(get_pg_connection(database_name))

    # Import CSV to PostgreSQL
    df.to_sql(table_name, engine, if_exists="replace", index=False)


# Example usage
if __name__ == "__main__":
    database_name = "sample_db_vj"
    # Create database if not exists
    # create_database(database_name)

    # Import CSV files to PostgreSQL
    table_files = {
        "table-1": "./data/table1.csv",
        "table-2": "./data/table2.csv",
    }

    for table_name, file_path in table_files.items():
        import_csv_to_pgsql(file_path, database_name, table_name)
