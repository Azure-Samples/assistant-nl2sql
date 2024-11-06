import os
from dotenv import load_dotenv
import json


class PGConfig:
    def __init__(self):
        load_dotenv(override=True)
        self.db_params = {
            "dbname": os.getenv("AZURE_POSTGRES_DATABASE"),
            "user": f"{os.getenv('AZURE_POSTGRES_USER')}",
            "password": os.getenv("AZURE_POSTGRES_PASSWORD"),
            "host": f"{os.getenv('AZURE_POSTGRES_SERVER')}"
            + ".postgres.database.azure.com",
            "port": 5432,
            "sslmode": "require",
        }
        self.verbose = True


# config = Config()


class BigQueryConfig:
    def __init__(self):
        load_dotenv(override=True)

        # Load BigQuery json directory path from .env file
        secret_name = os.getenv("SERVICE_ACCOUNT_SECRET_NAME")
        if not secret_name:
            raise ValueError("SERVICE_ACCOUNT_SECRET_NAME is not set in the environment variables.")

        # Construct the path to the secret file
        project_root = os.path.abspath(os.path.dirname(__file__))
        secret_file_path = os.path.join(project_root, "..", "..", "secrets", secret_name)

        # Check if the secret file exists
        if not os.path.isfile(secret_file_path):
            raise FileNotFoundError(f"Secret file {secret_file_path} does not exist.")

        self.service_account_json = secret_file_path
        self.dataset_id = os.getenv("BIGQUERY_DATASET_ID")
        self.project_id = json.load(open(self.service_account_json))["project_id"]


# bigquery_config = BigQueryConfig()
