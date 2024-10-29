# app.py
import os
import streamlit as st
import requests
from dotenv import load_dotenv
from openai import AzureOpenAI
from src.lib.event_handler import StreamlitEventHandler
from src.lib.assistant import AIAssistant
from src.lib.tools_bigquery import (
    GetDBSchema,
    RunSQLQuery,
    ListTables,
    FetchDistinctValues,
    FetchSimilarValues,
)
from src.lib.tools_search import FetchSimilarQueries
from src.lib.event_handler import StreamlitEventHandler
from openai import AzureOpenAI
import streamlit as st

# Create an Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

# Create a list of functions
functions = [
    GetDBSchema(),
    RunSQLQuery(),
    FetchDistinctValues(),
    FetchSimilarValues(),
    ListTables(),
    FetchSimilarQueries(),
]

# Load the tools
tools = [{"type": "function", "function": f.to_dict()} for f in functions]

# Load the instructions
instructions_path = os.path.join(
    os.path.dirname(__file__),
    "src",
    "instructions",
    "instructions_bigquery.jinja2",
)
instructions = open(instructions_path).read()

# Get the model
model = os.getenv("AZURE_OPENAI_MODEL_NAME")

# Create an AI Assistant
assistant = AIAssistant(
    client=client,
    verbose=True,
    name="AI Assistant",
    description="An AI Assistant",
    instrunctions=instructions,
    model=model,
    tools=tools,
    functions=functions,
)

FLASK_API_URL = os.getenv("FLASK_API_URL", "http://localhost:5000")

st.set_page_config(page_title="DAVE", page_icon="🕵️")

# Apply custom CSS
st.html(
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
        """
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
    event_handler = StreamlitEventHandler(st.session_state.text_boxes)

    # Make a request to the Flask server
    assistant.create_response_with_handler(
        question=prompt,
        event_handler=event_handler,
        thread_id=st.session_state.thread_id,
    )