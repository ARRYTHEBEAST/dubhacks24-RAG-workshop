import streamlit as st
from streamlit_chat import message
import random
import google.generativeai as genai
import os
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv
from tqdm import tqdm  # For progress bar in ChromaDB setup

load_dotenv()

MAX_CONTEXT = 5  # conversational memory window

#=====================================================#
#                      API SETUP                      #
#=====================================================#

# Gemini setup (replace with your specific system prompt)
system_prompt = "You are a helpful chatbot that assists users with various queries by retrieving relevant information from a recipe database."

# Configure Gemini API key
genai.configure(api_key="AIzaSyBeSeig1txnJMY22RgX4sH5WrgpRQvChv0")

# Initialize the Generative AI model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=system_prompt
)

# Embedding function for vector queries
google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
    api_key="AIzaSyBeSeig1txnJMY22RgX4sH5WrgpRQvChv0"
)

# ChromaDB client and collection
client = chromadb.PersistentClient(path="./data/vectorDB")
collection = client.get_collection(name="my_collection", embedding_function=google_ef)

#=====================================================#
#                     Chat Code                       #
#=====================================================#

# Storing the displayed messages
if 'past' not in st.session_state:
    st.session_state['past'] = ["Hello! How can I assist you today?"]

# Add default welcome message
if 'generated' not in st.session_state:
    st.session_state['generated'] = ["I'm here to help! Ask me anything about recipes."]

# Pick random avatar for the user and bot
if "avatars" not in st.session_state:
    st.session_state.avatars = {"user": random.randint(0, 100), "bot": random.randint(0, 100)}

# Storing conversation history for the LLM
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize chat model
llm = model.start_chat(history=st.session_state.messages)

# Function to query ChromaDB and return relevant document
def query_db(query, n_results=1):
    results = collection.query(query_texts=[query], n_results=n_results)
    return "\n".join(results["documents"][0]) if results["documents"] else "No relevant data found."

# Function to send a message to the LLM and update the UI
def chat(user_input=""):
    if user_input == "":
        user_input = st.session_state.input
    st.session_state.input = ""

    # Query ChromaDB to get the most relevant data based on user input
    retrieved_data = query_db(user_input)

    # Generate LLM response, passing the user input and retrieved data as context
    completion = llm.send_message(f'User input: {user_input}. Use this data to help: {retrieved_data}')

    # Add new user message and model response to the conversation history
    st.session_state.messages.append({"role": "user", "parts": user_input})
    st.session_state.messages.append({"role": "model", "parts": completion.text})

    # Keep the message history within the window limit
    if len(st.session_state.messages) > MAX_CONTEXT:
        st.session_state.messages = st.session_state.messages[:MAX_CONTEXT]

    # Update the chat UI
    st.session_state.generated.append(completion.text)
    st.session_state.past.append(user_input)

#=====================================================#
#               Streamlit UI Layout                   #
#=====================================================#

st.set_page_config(page_title="RAG Chatbot Demo", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")
st.header("RAG Chatbot Demo using Google Gemini and ChromaDB\n")

with st.sidebar:
    st.markdown("# About 🙌")
    st.markdown("This is a simple RAG chatbot demo that uses:")
    st.markdown("- Google Gemini")
    st.markdown("- ChromaDB")
    st.markdown("- Streamlit")
    st.markdown("---")

# Capture user input
input_text = st.text_input("Ask a question about recipes:",
                           placeholder="e.g., Show me a recipe with chicken", key="input", on_change=chat)

# Display the conversation
if st.session_state['generated']:
    for i in range(len(st.session_state['generated'])-1, -1, -1):
        if st.session_state['past'][i] != "":
            message(st.session_state['past'][i], is_user=True, avatar_style="adventurer", seed=st.session_state.avatars["user"], key=str(i) + '_user')
        message(st.session_state["generated"][i], seed=st.session_state.avatars["bot"], key=str(i))
