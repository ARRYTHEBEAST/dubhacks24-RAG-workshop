import streamlit as st
from streamlit_chat import message
import random
import google.generativeai as genai
import os
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv
import json

load_dotenv()

# File paths
PREFERENCES_FILE = "user_preferences.json"
INVENTORY_FILE = "inventory.json"
FAVORITE_PLANS_FILE = "favorite_meal_plans.json"

# Gemini setup
system_prompt = """
You are a helpful but sassy chatbot that assists users with meal planning by retrieving relevant information from a recipe database and using your general knowledge. 
You have a great sense of humor and aren't afraid to playfully tease users about their odd grocery combinations or off-topic questions. 
Your jokes should be witty but never mean-spirited. When users ask off-topic questions, gently mock them before answering.
"""

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

# Initialize chat model
llm = model.start_chat(history=[])

# User Preference Management
def load_preferences():
    if os.path.exists(PREFERENCES_FILE):
        with open(PREFERENCES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_preferences(preferences):
    with open(PREFERENCES_FILE, 'w') as f:
        json.dump(preferences, f, indent=2)

def update_preferences(dietary_restrictions, favorite_cuisines, allergies, health_goals):
    preferences = load_preferences()
    preferences.update({
        "dietary_restrictions": dietary_restrictions,
        "favorite_cuisines": favorite_cuisines,
        "allergies": allergies,
        "health_goals": health_goals
    })
    save_preferences(preferences)

def get_preferences_prompt():
    preferences = load_preferences()
    prompt = "User preferences: "
    prompt += f"Dietary restrictions: {', '.join(preferences.get('dietary_restrictions', []))}. "
    prompt += f"Favorite cuisines: {', '.join(preferences.get('favorite_cuisines', []))}. "
    prompt += f"Allergies: {', '.join(preferences.get('allergies', []))}. "
    prompt += f"Health goals: {', '.join(preferences.get('health_goals', []))}."
    return prompt

# Grocery and Inventory Management
def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        with open(INVENTORY_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_inventory(inventory):
    with open(INVENTORY_FILE, 'w') as f:
        json.dump(inventory, f, indent=2)

def update_inventory(grocery_list):
    inventory = load_inventory()
    for item, quantity in grocery_list.items():
        if item in inventory:
            inventory[item] += quantity
        else:
            inventory[item] = quantity
    save_inventory(inventory)

def get_inventory_prompt():
    inventory = load_inventory()
    return f"Current inventory: {', '.join([f'{item} ({quantity})' for item, quantity in inventory.items()])}"

# New function to generate humorous comments
def generate_humorous_comment(grocery_list, is_off_topic=False):
    prompt = f"""
    Generate a humorous comment based on the following scenario:
    
    Grocery list: {', '.join(grocery_list)}
    Is the user's question off-topic? {"Yes" if is_off_topic else "No"}

    The comment should be witty and playful, but not mean-spirited. If the question is off-topic, 
    gently tease the user before answering their question. If the grocery list is odd, make a joke about 
    their unusual combination of items.

    Example responses:
    - "Chicken, bananas, and milk? Are you planning a tropical smoothie nightmare?"
    - "Ah, I see you're going for the 'confused college student' diet. Bold choice!"
    - "Off-topic AND a weird grocery list? You're really keeping me on my toes today!"

    Please provide a humorous comment in a similar style:
    """
    completion = llm.send_message(prompt)
    return completion.text

# Modified function to include humor in meal plan generation
def generate_meal_plan(user_input, preferences, inventory):
    grocery_list = list(inventory.keys())
    humor_comment = generate_humorous_comment(grocery_list)

    prompt = f"""
    {humor_comment}

    Now, let's get back to business. Generate a detailed weekly meal plan based on the following information:
    {get_preferences_prompt()}
    {get_inventory_prompt()}
    User request: {user_input}

    The meal plan should include:
    - Breakfast, lunch, dinner, and snacks (if applicable) for each day of the week
    - Use ingredients from the current inventory when possible
    - Include nutritional information for each meal (calories, protein, carbs, fat)
    - Suggest recipes from the database when available, but also use your general knowledge
    - Be creative and diverse in meal selections
    - Occasionally add humorous comments about the meals or ingredients

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
    - Include occasional jokes or humorous comments about the meals or ingredients
    """

    db_results = collection.query(
        query_texts=[user_input + " " + get_preferences_prompt()],
        n_results=5
    )
    
    relevant_recipes = "\n".join(db_results["documents"][0]) if db_results["documents"] else "No relevant recipes found in the database."
    full_prompt = prompt + "\n\nRelevant recipes from the database:\n" + relevant_recipes

    completion = llm.send_message(full_prompt)
    return completion.text

# Meal Plan Customization
def customize_meal_plan(meal_plan, customization_request):
    prompt = f"""
    Original meal plan:
    {meal_plan}

    User customization request:
    {customization_request}

    Please modify the meal plan according to the user's request. Maintain the overall structure and nutritional balance of the plan while accommodating the changes. Include occasional humorous comments about the modifications.
    """
    completion = llm.send_message(prompt)
    return completion.text

# Modified function to handle off-topic questions with humor
def handle_followup_question(meal_plan, question):
    grocery_list = list(load_inventory().keys())
    is_off_topic = not any(food_related_word in question.lower() for food_related_word in ["food", "meal", "recipe", "ingredient", "cook", "eat"])
    humor_comment = generate_humorous_comment(grocery_list, is_off_topic)

    prompt = f"""
    {humor_comment}

    Now, regarding this meal plan:
    {meal_plan}

    User question:
    {question}

    Please provide a detailed answer to the user's question. If the question is about a specific recipe, provide more details about ingredients, preparation steps, or cooking techniques. If the information isn't available, use your general knowledge to provide a helpful response. Include occasional humorous comments in your answer.
    """
    completion = llm.send_message(prompt)
    return completion.text

# Favorite Meal Plans Management
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

# Streamlit UI
def main():
    st.set_page_config(page_title="Humorous Meal Planning Assistant", page_icon="🍽️", layout="wide", initial_sidebar_state="expanded")
    st.header("Humorous Meal Planning Assistant using Google Gemini and ChromaDB\n")

    # Sidebar for user preferences
    with st.sidebar:
        st.markdown("# User Preferences 🥗")
        preferences = load_preferences()
        dietary_restrictions = st.multiselect("Dietary Restrictions", ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free"], default=preferences.get("dietary_restrictions", []))
        favorite_cuisines = st.multiselect("Favorite Cuisines", ["Italian", "Mexican", "Chinese", "Indian", "Japanese"], default=preferences.get("favorite_cuisines", []))
        allergies = st.text_input("Allergies (comma-separated)", value=", ".join(preferences.get("allergies", [])))
        health_goals = st.multiselect("Health Goals", ["Weight loss", "Muscle gain", "Heart health", "Diabetes management"], default=preferences.get("health_goals", []))

        if st.button("Update Preferences"):
            update_preferences(dietary_restrictions, favorite_cuisines, allergies.split(','), health_goals)
            st.success("Preferences updated! Hope you're ready for some culinary adventures!")

    # Main area for grocery input and meal planning
    st.markdown("## Weekly Grocery Input 🛒")
    grocery_items = st.text_area("Enter your grocery items (one per line, format: item,quantity)")
    if st.button("Update Inventory"):
        grocery_list = {}
        for line in grocery_items.split('\n'):
            if line.strip():
                item, quantity = line.split(',')
                grocery_list[item.strip()] = float(quantity.strip())
        update_inventory(grocery_list)
        st.success("Inventory updated! Let's see what culinary chaos we can create with this!")

    st.markdown("## Meal Plan Generation 📅")
    user_input = st.text_input("Any specific requests for your meal plan? Don't be shy, surprise me!")
    if st.button("Generate Meal Plan"):
        preferences = load_preferences()
        inventory = load_inventory()
        meal_plan = generate_meal_plan(user_input, preferences, inventory)
        st.session_state.current_meal_plan = meal_plan
        st.write(meal_plan)

    # Meal plan customization
    if 'current_meal_plan' in st.session_state:
        st.markdown("### Customize Meal Plan 🔧")
        customization_request = st.text_input("Enter your customization request (I promise I won't judge... much):")
        if st.button("Customize Plan"):
            customized_plan = customize_meal_plan(st.session_state.current_meal_plan, customization_request)
            st.session_state.current_meal_plan = customized_plan
            st.write(customized_plan)

        st.markdown("### Ask a Follow-up Question ❓")
        followup_question = st.text_input("Enter your question about the meal plan (or anything else, I'm flexible):")
        if st.button("Ask Question"):
            answer = handle_followup_question(st.session_state.current_meal_plan, followup_question)
            st.write(answer)

        st.markdown("### Save Favorite Meal Plan ⭐")
        plan_name = st.text_input("Enter a name for this meal plan (make it catchy!):")
        if st.button("Save Plan"):
            add_favorite_plan(plan_name, st.session_state.current_meal_plan)
            st.success(f"Meal plan '{plan_name}' saved! It's now immortalized in the hall of culinary fame!")

    st.markdown("## Load Favorite Meal Plan 📂")
    favorite_plans = load_favorite_plans()
    selected_plan = st.selectbox("Select a favorite meal plan (choose wisely):", list(favorite_plans.keys()))
    if st.button("Load Plan"):
        loaded_plan = get_favorite_plan(selected_plan)
        st.session_state.current_meal_plan = loaded_plan
        st.write(loaded_plan)

if __name__ == "__main__":
    main()