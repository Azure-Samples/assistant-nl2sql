import os
from dotenv import load_dotenv

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