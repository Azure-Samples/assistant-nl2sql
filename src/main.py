import os
from openai import AzureOpenAI
from lib.assistant import AIAssistant
from lib.tools import GetDBSchema, RunSQLQuery, FetchDistinctValues, FetchSimilarValues, ListTables

class SQLAssistant:
    def __init__(self):
        self.functions = [
            GetDBSchema(), 
            RunSQLQuery(), 
            FetchDistinctValues(), 
            FetchSimilarValues(), 
            ListTables()
        ]
        self.tools = [{"type": "function", "function": f.to_dict()} for f in self.functions]
        self.client = self.create_client()
        self.instructions = self.load_instructions()
        self.model = os.getenv("AZURE_OPENAI_MODEL_NAME")
        self.assistant = self.create_assistant()

    def create_client(self):
        return AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_KEY"), 
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"), 
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )

    def load_instructions(self):
        instructions_path = os.path.join(os.path.dirname(__file__), "instructions", "instructions.jinja2")
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
            functions=self.functions
        )

    def chat(self):
        self.assistant.chat()

# Main function
if __name__ == "__main__":
    sql_assistant = SQLAssistant()
    sql_assistant.chat()
