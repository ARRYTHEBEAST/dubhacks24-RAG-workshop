import json
import os
import streamlit as st
PREFERENCES_FILE = "user_preferences.json"

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

# Add this to your Streamlit UI
st.sidebar.header("User Preferences")
dietary_restrictions = st.sidebar.multiselect("Dietary Restrictions", ["Vegetarian", "Vegan", "Gluten-free", "Dairy-free"])
favorite_cuisines = st.sidebar.multiselect("Favorite Cuisines", ["Italian", "Mexican", "Chinese", "Indian", "Japanese"])
allergies = st.sidebar.text_input("Allergies (comma-separated)")
health_goals = st.sidebar.multiselect("Health Goals", ["Weight loss", "Muscle gain", "Heart health", "Diabetes management"])

if st.sidebar.button("Update Preferences"):
    update_preferences(dietary_restrictions, favorite_cuisines, allergies.split(','), health_goals)
    st.sidebar.success("Preferences updated!")