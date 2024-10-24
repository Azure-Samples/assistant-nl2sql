import os
from dotenv import load_dotenv
import json

class Config:
    def __init__(self):
        load_dotenv(override=True)
        self.db_params = {
            'dbname': os.getenv('AZURE_POSTGRES_DATABASE'),
            'user': f"{os.getenv('AZURE_POSTGRES_USER')}",
            'password': os.getenv('AZURE_POSTGRES_PASSWORD'),
            'host': f"{os.getenv('AZURE_POSTGRES_SERVER')}" + ".postgres.database.azure.com",
            'port': 5432,
            'sslmode': 'require'
        }
        self.verbose = True

config = Config()

class BigQueryConfig:
    def __init__(self):
        load_dotenv(override=True)

        # Load BigQuery json directory path from .env file
        self.keys_dir = os.getenv('SERVICE_ACCOUNT_JSON_PATH')
        project_root = os.path.abspath(os.path.dirname(__file__))
        self.keys_dir = os.path.join(project_root, ".." ,self.keys_dir)

        # Check if the directory exists
        if not os.path.isdir(self.keys_dir):
            raise NotADirectoryError(f"Service account JSON directory not found at {self.keys_dir}")

        # Find the JSON file in the directory
        json_files = [f for f in os.listdir(self.keys_dir) if f.endswith('.json')]
        if not json_files:
            raise FileNotFoundError(f"No JSON files found in directory {self.keys_dir}")

        self.keys_path = os.path.join(self.keys_dir, json_files[0])

        # Open and load the JSON file
        try:
            with open(self.keys_path, 'r') as json_file:
                self.service_account_json = json.load(json_file)
                self.dataset_id = os.getenv('BIGQUERY_DATASET_ID')
        except json.JSONDecodeError:
            raise ValueError(f"File at {self.keys_path} is not a valid JSON file")
        

bigquery_config = BigQueryConfig()