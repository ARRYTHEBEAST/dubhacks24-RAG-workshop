import gradio as gr
import random
import google.generativeai as genai
import chromadb
import chromadb.utils.embedding_functions as embedding_functions
from dotenv import load_dotenv

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
#               Chat and Database Logic               #
#=====================================================#

# Initialize the conversation history
chat_history = []

# Function to query ChromaDB and return relevant document
def query_db(query, n_results=1):
    results = collection.query(query_texts=[query], n_results=n_results)
    return "\n".join(results["documents"][0]) if results["documents"] else "No relevant data found."

def chatbot(input_text, history):
    chat_history = history or []
    
    # Convert chat history to the expected format
    chat_history = convert_chat_history(chat_history)
    
    chat_history.append({'role': 'user', 'content': input_text})
    
    # Pass the converted history to the model
    llm = model.start_chat(history=chat_history)
    response = llm.send_message(input_text)
    
    chat_history.append({'role': 'assistant', 'content': response['content']})
    return response['content'], chat_history

#=====================================================#
#                 Gradio UI Layout                    #
#=====================================================#

# Define the Gradio interface
with gr.Blocks() as demo:
    # Title
    gr.Markdown("# RAG Chatbot Demo using Google Gemini and ChromaDB\n")
    
    # Create chatbot UI using `messages` format
    chatbot_output = gr.Chatbot(label="Recipe Assistant", type="messages")
 
    # Input text box
    user_input = gr.Textbox(label="Ask a question about recipes", placeholder="e.g., Show me a recipe with chicken")

    # Set up chat button
    submit_btn = gr.Button("Send")

    # Store chat history
    chat_history_state = gr.State([])  # To store conversation history

    # Define interaction between components
    submit_btn.click(
        chatbot,
        inputs=[user_input, chat_history_state],
        outputs=[chatbot_output, chat_history_state],
        show_progress=True,
    )

    from google.generativeai.types import content_types

def convert_chat_history(chat_history):
    converted_history = []
    for message in chat_history:
        if message['role'] == 'user':
            content = {'parts': [{'text': message['content'], 'inline_data': {}}]}
        else:
            content = {'parts': [{'text': message['content'], 'inline_data': {}}]}
        converted_history.append(content)
    return converted_history




# Launch the Gradio app
demo.launch(share=True)
