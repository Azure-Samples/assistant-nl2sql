# app.py
import os
import streamlit as st
import requests
from dotenv import load_dotenv
from openai import AzureOpenAI
from src.lib.event_handler import StreamlitEventHandler
from src.lib.assistant import AIAssistant
from src.lib.tools_bigquery import (
    GetDBSchema as GetDBSchemaBigQuery,
    RunSQLQuery as RunSQLQueryBigQuery,
    ListTables as ListTablesBigQuery,
    FetchDistinctValues as FetchDistinctValuesBigQuery,
    FetchSimilarValues as FetchSimilarValuesBigQuery,
)
from src.lib.tools_postgres import (
    GetDBSchema as GetDBSchemaPostgres,
    RunSQLQuery as RunSQLQueryPostgres,
    ListTables as ListTablesPostgres,
    FetchDistinctValues as FetchDistinctValuesPostgres,
    FetchSimilarValues as FetchSimilarValuesPostgres,
)
from src.lib.tools_search import FetchSimilarQueries

# Load environment variables
load_dotenv()

# Initialize the tools and instructions based on the database parameter
def initialize_tools_and_instructions(database):
    if database == "bigquery":
        functions = [
            GetDBSchemaBigQuery(),
            RunSQLQueryBigQuery(),
            FetchDistinctValuesBigQuery(),
            FetchSimilarValuesBigQuery(),
            ListTablesBigQuery(),
            FetchSimilarQueries(),
        ]
        instructions_path = os.path.join(
            os.path.dirname(__file__),
            "src",
            "instructions",
            "instructions_bigquery.jinja2",
        )
    elif database == "postgresql":
        functions = [
            GetDBSchemaPostgres(),
            RunSQLQueryPostgres(),
            FetchDistinctValuesPostgres(),
            FetchSimilarValuesPostgres(),
            ListTablesPostgres(),
            FetchSimilarQueries(),
        ]
        instructions_path = os.path.join(
            os.path.dirname(__file__),
            "src",
            "instructions",
            "instructions_postgres.jinja2",
        )
    else:
        raise ValueError("Unsupported database type. Choose either 'bigquery' or 'postgresql'.")

    tools = [{"type": "function", "function": f.to_dict()} for f in functions]
    instructions = open(instructions_path).read()

    return functions, tools, instructions


def initialize_assistant(database):
    # Initialize tools and instructions based on the database parameter
    functions, tools, instructions = initialize_tools_and_instructions(database)

    # Create an Azure OpenAI client
    client = AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    )

    # Get the model
    model = os.getenv("AZURE_OPENAI_MODEL_NAME")

    # Create an AI Assistant
    assistant = AIAssistant(
        client=client,
        verbose=True,
        name="AI Assistant",
        description="An AI Assistant",
        instructions=instructions,
        model=model,
        tools=tools,
        functions=functions,
    )

    return assistant

# Set the page title and icon
st.set_page_config(page_title="BigAssistant", page_icon="🕵️")

# Get the database parameter from the query string
database = st.sidebar.selectbox('What is your database?',
                                    ['postgresql', 'bigquery'])

# Initialize the assistant
assistant = initialize_assistant(database)

# Apply custom CSS
st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden}
        #header {visibility: hidden}
        #footer {visibility: hidden}
        .block-container {
            padding-top: 3rem;
            padding-bottom: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize the questions list
if "prompt" not in st.session_state:
    st.session_state.questions = []

# UI
st.subheader("🔮 Chat with your Data Assistant")
st.markdown(
    "You can ask questions about your data and get answers in real-time.",
)

# Local history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    thread = assistant.create_thread()
    st.session_state.thread_id = thread.id
    st.session_state.assistant_id = assistant.assistant_id

if "text_boxes" not in st.session_state:
    st.session_state.text_boxes = []

if prompt := st.chat_input("Ask me a question about your dataset"):
    st.session_state.messages.append(
        {"role": "user", "items": [{"type": "text", "content": prompt}]}
    )

    st.session_state.text_boxes.append(st.empty())
    st.session_state.text_boxes[-1].success(f"**> 🤔 User:** {prompt}")

    assistant.create_message(
        thread_id=st.session_state.thread_id, 
        role="user", 
        question=prompt
    )

    # Create the event handler
    event_handler = StreamlitEventHandler(st.session_state.text_boxes, verbose=False)

    # Make a request to the Flask server
    assistant.create_response_with_handler(
        question=prompt,
        event_handler=event_handler,
        thread_id=st.session_state.thread_id,
        verbose=True,
    )