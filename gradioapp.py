import gradio as gr
import os

# Function to handle the "make me something" input and sliders
def handle_submission(chat_input, calorie_input, thrill_slider, salt_slider, sugar_slider, image_upload):
    # Format the data into a string
    data = f"""
    Request: {chat_input}
    Calories: {calorie_input if calorie_input else "Not provided"}
    Thrill Slider: {thrill_slider}
    Salt Slider: {salt_slider}
    Sugar Slider: {sugar_slider}
    Image Uploaded: {'Yes' if image_upload else 'No'}
    """

    # Save the data to a text file in the local project directory
    with open("submission_data.txt", "a") as file:
        file.write(data)
        file.write("\n" + "-"*50 + "\n")  # Add a separator between entries

    return "Data has been saved successfully!"

# Function to enable/disable sliders based on "make me something" input
def toggle_fields(chat_input):
    # Enable sliders if there's any input in the chat field
    if chat_input:
        return gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)
    else:
        return gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)

# Function to enable/disable submit button
def toggle_submit(chat_input, image_upload):
    return gr.update(interactive=bool(chat_input) or image_upload is not None)

# Create interface
with gr.Blocks() as demo:
    
    # Title
    gr.Markdown("# Make Me Something Bot")
    
    # Chat input field
    chat_input = gr.Textbox(label="Make me something", placeholder="Enter a request for the chatbot...", lines=3)
    
    # Image upload field
    image_upload = gr.Image(label="Upload an image", type="pil")
    
    # Calorie input and toggle
    calorie_toggle = gr.Checkbox(label="Enable calorie input")
    calorie_input = gr.Number(label="Daily Calories", visible=False)
    
    def toggle_calorie_field(enable_calorie):
        return gr.update(visible=enable_calorie)
    
    # Connect calorie toggle to visibility of calorie input
    calorie_toggle.change(toggle_calorie_field, inputs=calorie_toggle, outputs=calorie_input)

    # Sliders toggles
    slider_toggle = gr.Checkbox(label="Enable sliders")
    
    # Health sliders
    thrill_slider = gr.Slider(minimum=0.03, maximum=1, step=0.01, value=0.5, label="How healthy do you want to be?", interactive=False)
    salt_slider = gr.Slider(minimum=0.03, maximum=1, step=0.01, value=0.5, label="Salt Level", interactive=False)
    sugar_slider = gr.Slider(minimum=0.03, maximum=1, step=0.01, value=0.5, label="Sugar Level", interactive=False)
    
    # Define custom labels for the extreme sides
    gr.Markdown("### Health Slider: Thrill Seeker (Right) to Live to 100 (Left)")
    gr.Markdown("### Salt Slider: The Ocean (Right) to Heart Smart (Left)")
    gr.Markdown("### Sugar Slider: Sugary (Right) to Minimal Sugar (Left)")
    
    # Disable sliders unless "make me something" field is filled
    chat_input.change(toggle_fields, inputs=chat_input, outputs=[thrill_slider, salt_slider, sugar_slider])

    # Submit button
    submit_button = gr.Button("Submit", interactive=False)

    # Enable/disable submit button based on conditions
    chat_input.change(toggle_submit, inputs=[chat_input, image_upload], outputs=submit_button)
    image_upload.change(toggle_submit, inputs=[chat_input, image_upload], outputs=submit_button)
    
    # Message to confirm data saving
    output_text = gr.Textbox(label="Status", interactive=False)

    # Submit action, save data to file and show status message
    submit_button.click(handle_submission, inputs=[chat_input, calorie_input, thrill_slider, salt_slider, sugar_slider, image_upload], outputs=output_text)

# Launch the app
demo.launch(share=True)