from .function import Function, Property
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
import os
from dotenv import load_dotenv

class FetchSimilarQueries(Function):
    def __init__(self):
        load_dotenv(override=True)
        super().__init__(
            name="fetch_similar_queries",
            description="Fetch the most similar queries to a given query",
            parameters=[
                Property(
                    name="query",
                    description="The query to find similar queries",
                    type="string",
                    required=True,
                )
            ]
        )

        self.aoai_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            api_key=os.getenv("AZURE_OPENAI_KEY")
        )

        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL_NAME")

        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT"),
            index_name=os.getenv("AZURE_SEARCH_ADMIN_KEY"),
            credential=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        )

    def get_embedding(self, text) -> list:
        return (
            self.aoai_client.embeddings.create(input=text, model=self.embedding_deployment)
            .data[0]
            .embedding
        )
    
    def function(self, user_question):
        try:
            search_vector = self.get_embedding(user_question)
            result = self.search_client.search(
                user_question,
                top=5,
                vector_queries=[
                    VectorizedQuery(vector=search_vector, k=50, fields="vector")
                ],
                query_type="semantic",
                semantic_configuration_name="documents-index-semantic-config",
            )

            docs = [
                {
                    "question": doc["question"],
                    "bigquery": doc["bigquery"]
                }
                for doc in result
            ]

            result = """Examples of similar User Questions with their corresponding BigQuery:\n"""
            result += "\n\n".join(
                [f"User Question: {doc['question']}\nBigQuery: {doc['bigquery']}" for doc in docs]
            )
            
            return result
        
        except Exception as e:
            return f"Error fetching similar queries: {e}"