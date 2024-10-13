import streamlit as st
from streamlit_chat import message
import random
import google.generativeai as genai
import os
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv

from user_preference_management import load_preferences, save_preferences, update_preferences, get_preferences_prompt
from grocery_inventory_management import load_inventory, save_inventory, update_inventory, get_inventory_prompt
#from meal_plan_customization import customize_meal_plan, handle_followup_question
#from favorite_meal_plans import load_favorite_plans, save_favorite_plans, add_favorite_plan, get_favorite_plan


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

# Function to query ChromaDB and return relevant recipes
def query_recipes(available_items, dietary_restrictions, favorite_cuisines):
    # Constructing the query
    query = "Available ingredients: " + ", ".join(available_items) + ". "
    query += "Dietary restrictions: " + ", ".join(dietary_restrictions) + ". "
    query += "Preferred cuisines: " + ", ".join(favorite_cuisines) + ". "
    
    # Querying ChromaDB for relevant recipes
    results = collection.query(query_texts=[query], n_results=5)
    return results["documents"] if results["documents"] else []

# Function to query ChromaDB for general questions
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

    # Query ChromaDB for relevant recipes
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


def generate_meal_plan(user_input, preferences, inventory):
    # Construct the prompt
    prompt = f"""
    Generate a detailed weekly meal plan based on the following information:
    {get_preferences_prompt()}
    {get_inventory_prompt()}
    User request: {user_input}

    The meal plan should include:
    - Breakfast, lunch, dinner, and snacks (if applicable) for each day of the week
    - Use ingredients from the current inventory when possible
    - Include nutritional information for each meal
    - Suggest recipes from the database when available, but also use your general knowledge
    - Be creative and diverse in meal selections

    Format the meal plan as follows:
    Monday:
    - Breakfast: [Meal name] (Nutritional info: calories, protein, carbs, fat)
    - Lunch: [Meal name] (Nutritional info: calories, protein, carbs, fat)
    - Dinner: [Meal name] (Nutritional info: calories, protein, carbs, fat)
    - Snacks: [Snack names if applicable]

    [Repeat for each day of the week]

    Additional suggestions:
    - List any missing ingredients that would enhance the meal plan
    - Provide tips for meal prep or cooking techniques
    """

    # Query ChromaDB for relevant recipes
    db_results = query_recipes(user_input, preferences, inventory)
    
    # Combine ChromaDB results with the prompt
    full_prompt = prompt + "\n\nRelevant recipes from the database:\n" + "\n".join(db_results)

    # Generate the meal plan using the LLM
    completion = llm.send_message(full_prompt)
    return completion.text

# Modify the Streamlit UI
st.header("Meal Plan Generation")
user_input = st.text_input("Any specific requests for your meal plan?")
if st.button("Generate Meal Plan"):
    preferences = load_preferences()
    inventory = load_inventory()
    meal_plan = generate_meal_plan(user_input, preferences, inventory)
    st.write(meal_plan)

def customize_meal_plan(meal_plan, customization_request):
    prompt = f"""
    Original meal plan:
    {meal_plan}

    User customization request:
    {customization_request}

    Please modify the meal plan according to the user's request. Maintain the overall structure and nutritional balance of the plan while accommodating the changes.
    """
    completion = llm.send_message(prompt)
    return completion.text

def handle_followup_question(meal_plan, question):
    prompt = f"""
    Regarding this meal plan:
    {meal_plan}

    User question:
    {question}

    Please provide a detailed answer to the user's question. If the question is about a specific recipe, provide more details about ingredients, preparation steps, or cooking techniques. If the information isn't available, use your general knowledge to provide a helpful response.
    """
    completion = llm.send_message(prompt)
    return completion.text

# Add these to your Streamlit UI
st.subheader("Customize Meal Plan")
customization_request = st.text_input("Enter your customization request:")
if st.button("Customize Plan"):
    customized_plan = customize_meal_plan(meal_plan, customization_request)
    st.write(customized_plan)

st.subheader("Ask a Follow-up Question")
followup_question = st.text_input("Enter your question about the meal plan:")
if st.button("Ask Question"):
    answer = handle_followup_question(meal_plan, followup_question)
    st.write(answer)


import json
import os

FAVORITE_PLANS_FILE = "favorite_meal_plans.json"

def load_favorite_plans():
    if os.path.exists(FAVORITE_PLANS_FILE):
        with open(FAVORITE_PLANS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_favorite_plans(favorite_plans):
    with open(FAVORITE_PLANS_FILE, 'w') as f:
        json.dump(favorite_plans, f, indent=2)

def add_favorite_plan(plan_name, meal_plan):
    favorite_plans = load_favorite_plans()
    favorite_plans[plan_name] = meal_plan
    save_favorite_plans(favorite_plans)

def get_favorite_plan(plan_name):
    favorite_plans = load_favorite_plans()
    return favorite_plans.get(plan_name)

# Add these to your Streamlit UI
st.subheader("Save Favorite Meal Plan")
plan_name = st.text_input("Enter a name for this meal plan:")
if st.button("Save Plan"):
    add_favorite_plan(plan_name, meal_plan)
    st.success(f"Meal plan '{plan_name}' saved!")

st.subheader("Load Favorite Meal Plan")
favorite_plans = load_favorite_plans()
selected_plan = st.selectbox("Select a favorite meal plan:", list(favorite_plans.keys()))
if st.button("Load Plan"):
    loaded_plan = get_favorite_plan(selected_plan)
    st.write(loaded_plan)