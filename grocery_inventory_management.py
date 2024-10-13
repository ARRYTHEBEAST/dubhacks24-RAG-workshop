import json
import os
import streamlit as st
INVENTORY_FILE = "inventory.json"

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

# Add this to your Streamlit UI
st.header("Weekly Grocery Input")
grocery_items = st.text_area("Enter your grocery items (one per line, format: item,quantity)")
if st.button("Update Inventory"):
    grocery_list = {}
    for line in grocery_items.split('\n'):
        if line.strip():
            item, quantity = line.split(',')
            grocery_list[item.strip()] = float(quantity.strip())
    update_inventory(grocery_list)
    st.success("Inventory updated!")