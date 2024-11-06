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
from lib.tools_search import FetchSimilarQueries


class SQLAssistant:
    def __init__(self, functions, instructions_file_name):
        self.functions = functions
        self.tools = [
            {"type": "function", "function": f.to_dict()} for f in self.functions
        ]
        self.client = self.create_client()
        self.instructions_file_name = instructions_file_name
        self.instructions = self.load_instructions()
        self.model = os.getenv("AZURE_OPENAI_MODEL_NAME")
        self.assistant = self.create_assistant()

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
            instructions=self.instructions,
            model=self.model,
            tools=self.tools,
            functions=self.functions,
        )

    def chat(self):
        self.assistant.chat()


# Create a method to initialize the assistant based on the database type
def initialize_assistant(database_type):
    if database_type == "postgresql":
        sql_functions = [
            GetDBSchema(),
            RunSQLQuery(),
            FetchDistinctValues(),
            FetchSimilarValues(),
            ListTables(),
            FetchSimilarQueries(),
        ]
        instructions_file = "instructions_postgres.jinja2"
    elif database_type == "bigquery":
        sql_functions = [
            BigQueryGetDBSchema(),
            BigQueryRunSQLQuery(),
            BigQueryFetchDistinctValues(),
            BigQueryFetchSimilarValues(),
            BigQueryListTables(),
            FetchSimilarQueries(),
        ]
        instructions_file = "instructions_bigquery.jinja2"
    else:
        raise ValueError(f"Unsupported database type: {database_type}")

    return SQLAssistant(sql_functions, instructions_file)

# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQL Assistant")
    parser.add_argument(
        "--database",
        choices=["postgresql", "bigquery"],
        required=True,
        help="Specify the database type: 'postgresql' or 'bigquery'",
    )
    args = parser.parse_args()
    sql_assistant = initialize_assistant(args.database)
    sql_assistant.chat()
