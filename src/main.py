import os
from openai import AzureOpenAI
from lib.assistant import AIAssistant
import argparse
from lib.tools_postgres import (
    GetDBSchema,
    RunSQLQuery,
    FetchDistinctValues,
    FetchSimilarValues,
    ListTables,
)
from lib.tools_bigquery import (
    GetDBSchema as BigQueryGetDBSchema,
    RunSQLQuery as BigQueryRunSQLQuery,
    FetchDistinctValues as BigQueryFetchDistinctValues,
    FetchSimilarValues as BigQueryFetchSimilarValues,
    ListTables as BigQueryListTables,
)


class SQLAssistant:
    def __init__(self, functions, instractions_file_name):
        self.functions = functions
        self.tools = [
            {"type": "function", "function": f.to_dict()} for f in self.functions
        ]
        self.client = self.create_client()
        self.instructions = self.load_instructions()
        self.model = os.getenv("AZURE_OPENAI_MODEL_NAME")
        self.assistant = self.create_assistant()
        self.instructions_file_name = instractions_file_name

    def create_client(self):
        return AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        )

    def load_instructions(self):
        instructions_path = os.path.join(
            os.path.dirname(__file__), "instructions", self.instructions_file_name
        )
        with open(instructions_path) as file:
            return file.read()

    def create_assistant(self):
        return AIAssistant(
            client=self.client,
            verbose=True,
            name="AI Assistant",
            description="An AI Assistant",
            instrunctions=self.instructions,
            model=self.model,
            tools=self.tools,
            functions=self.functions,
        )

    def chat(self):
        self.assistant.chat()


# Create Postgres Assistant
sql_functions = [
    GetDBSchema(),
    RunSQLQuery(),
    FetchDistinctValues(),
    FetchSimilarValues(),
    ListTables(),
]
postgres_assistant = SQLAssistant(sql_functions, "instructions_postgres.jinja2")


# Create BigQuery Assistant
bigquery_functions = [
    BigQueryGetDBSchema(),
    BigQueryRunSQLQuery(),
    BigQueryFetchDistinctValues(),
    BigQueryFetchSimilarValues(),
    BigQueryListTables(),
]
bigquery_assistant = SQLAssistant(bigquery_functions, "instructions_bigquery.jinja2")

# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQL Assistant")
    parser.add_argument(
        "--database",
        choices=["postgres", "bigquery"],
        required=True,
        help="Specify the database type: 'postgres' or 'bigquery'",
    )
    args = parser.parse_args()
    if args.database == "postgres":
        sql_assistant = postgres_assistant
    elif args.database == "bigquery":
        sql_assistant = bigquery_assistant
    sql_assistant = SQLAssistant()
    sql_assistant.chat()
