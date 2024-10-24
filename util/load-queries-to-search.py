import os
import csv
import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv
import uuid
from openai import AzureOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureSearchIndexer:
    def __init__(self):
        load_dotenv(override=True)
        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMIN_KEY")),
        )

        self.aoai_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            api_key=os.getenv("AZURE_OPENAI_KEY")
        )

        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL_NAME")

    def get_embedding(self, text) -> list:
        logger.info(f"Generating embedding for text...")
        embedding = self.aoai_client.embeddings.create(input=text, model=self.embedding_deployment).data[0].embedding
        return embedding
    
    def insert_data(self, data_file):
        logger.info(f"Reading data from file: {data_file}")
        documents = []
        with open(data_file, "r") as file:
            reader = csv.reader(file, delimiter=',')
            next(reader)  
            for row in reader:
                question = row[0].replace('"""','')
                query = row[1].replace('"""','')

                logger.info("Processing row...")

                document = {
                    "id": str(uuid.uuid4()),
                    "question": question,
                    "vector": self.get_embedding(question),
                    "bigquery": query
                }

                documents.append(document)

        logger.info(f"Uploading {len(documents)} documents to Azure Search")
        try:
            result = self.search_client.upload_documents(documents=documents)
            logger.info("Documents indexed successfully")
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")

if __name__ == "__main__":
    indexer = AzureSearchIndexer()
    indexer.insert_data("./data/example_bigqueries.csv")
