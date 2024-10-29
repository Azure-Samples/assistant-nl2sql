from .function import Function, Property
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizedQuery
from openai import AzureOpenAI
import os
from dotenv import load_dotenv


class FetchSimilarQueries(Function):
    def __init__(self):
        load_dotenv(override=True)
        super().__init__(
            name="fetch_similar_queries",
            description="Fetch similar user questions and their corresponding queries.",
            parameters=[
                Property(
                    name="question",
                    description="The user question to find similar queries. In the same language as the user question.",
                    type="string",
                    required=True,
                )
            ],
        )

    def get_embedding(self, text) -> list:
        aoai_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
        )
        embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL_NAME")
        return (
            aoai_client.embeddings.create(input=text, model=embedding_deployment)
            .data[0]
            .embedding
        )

    def function(self, question):
        search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_SERVICE_ENDPOINT"),
            index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_ADMIN_KEY")),
        )
        try:
            search_vector = self.get_embedding(question)
            result = search_client.search(
                question,
                top=3,
                vector_queries=[VectorizedQuery(vector=search_vector, fields="vector")],
                query_type="semantic",
                semantic_configuration_name="documents-index-semantic-config",
            )

            docs = [
                {"question": doc["question"], "query": doc["query"]} for doc in result
            ]

            result = """Examples of similar User Questions with their corresponding BigQuery:\n"""
            result += "\n\n".join(
                [
                    f"User Question: {doc['question']}\n\n Query: {doc['query']}"
                    for doc in docs
                ]
            )

            return result

        except Exception as e:
            return f"Error fetching similar queries: {e}"
