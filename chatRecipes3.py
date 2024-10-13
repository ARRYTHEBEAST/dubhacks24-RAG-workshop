import streamlit as st
from streamlit_chat import message
import random
import google.generativeai as genai
import os
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv

load_dotenv()

MAX_CONTEXT = 5  # conversational memory window

#=====================================================#
#                      API SETUP                      #
#=====================================================#

# Gemini setup
system_prompt = "You are a knowledgeable chatbot that provides answers to various queries and can use recipe data when relevant."

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

if 'generated' not in st.session_state:
    st.session_state['generated'] = ["I'm here to help! Ask me anything about recipes."]

if "avatars" not in st.session_state:
    st.session_state.avatars = {"user": random.randint(0, 100), "bot": random.randint(0, 100)}

if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to query ChromaDB and return relevant recipes
def query_recipes(available_items, dietary_restrictions, favorite_cuisines):
    query = "Available ingredients: " + ", ".join(available_items) + ". "
    query += "Dietary restrictions: " + ", ".join(dietary_restrictions) + ". "
    query += "Preferred cuisines: " + ", ".join(favorite_cuisines) + ". "
    
    results = collection.query(query_texts=[query], n_results=5)
    return results["documents"] if results["documents"] else []

# Function to query ChromaDB for general questions
def query_db(query, n_results=1):
    results = collection.query(query_texts=[query], n_results=n_results)
    return results["documents"] if results["documents"] else []

# Function to send a message to the LLM and update the UI
def chat(user_input=""):
    if user_input == "":
        user_input = st.session_state.input
    st.session_state.input = ""

    # First, query the database for relevant recipes
    retrieved_data = query_db(user_input)

    # Flatten retrieved_data if it's a list of lists
    flattened_data = [doc for sublist in retrieved_data for doc in sublist] if isinstance(retrieved_data, list) else []

    # Create a contextual message
    context_message = f'User input: {user_input}. '
    if flattened_data:
        context_message += f'Here are some related recipes: {", ".join(flattened_data)}. '

    # Generate response using the core model with context
    completion = model.generate(prompt=context_message)  # Use the correct method here

    # Add new user message and model response to the conversation history
    st.session_state.messages.append({"role": "user", "parts": user_input})
    st.session_state.messages.append({"role": "model", "parts": completion.text})  # Adjust this based on what the generate method returns

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

# Capture user input for meal planning
st.sidebar.header("Meal Plan Generator")
available_items = st.sidebar.text_input("Available ingredients (comma-separated):", "")
dietary_restrictions = st.sidebar.text_input("Dietary Restrictions (comma-separated):", "")
favorite_cuisines = st.sidebar.text_input("Favorite Cuisines (comma-separated):", "")

# Button to generate meal plan
if st.sidebar.button("Generate Meal Plan"):
    available_items_list = [item.strip() for item in available_items.split(",") if item.strip()]
    dietary_restrictions_list = [restriction.strip() for restriction in dietary_restrictions.split(",") if restriction.strip()]
    favorite_cuisines_list = [cuisine.strip() for cuisine in favorite_cuisines.split(",") if cuisine.strip()]

    meal_plan = query_recipes(available_items_list, dietary_restrictions_list, favorite_cuisines_list)

    if meal_plan:
        st.sidebar.write("Here are your meal suggestions:")
        for meal in meal_plan:
            st.sidebar.write(f"- {meal}")  # Display the recipe name or relevant info
    else:
        st.sidebar.write("No meal plans match your criteria.")

# Capture user input for chat
input_text = st.text_input("Ask a question about recipes:", placeholder="e.g., Show me a recipe with chicken", key="input", on_change=chat)

# Display the conversation
if st.session_state['generated']:
    for i in range(len(st.session_state['generated'])-1, -1, -1):
        if st.session_state['past'][i] != "":
            message(st.session_state['past'][i], is_user=True, avatar_style="adventurer", seed=st.session_state.avatars["user"], key=str(i) + '_user')
        message(st.session_state["generated"][i], seed=st.session_state.avatars["bot"], key=str(i))
