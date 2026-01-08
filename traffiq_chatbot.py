import requests
import gradio as gr
import json

API_URL = "http://localhost:8000/query"


def chat_fn(message, history):
    if history is None:
        history = []

    # Call the API
    payload = {"question": message}
    
    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        
        if resp.status_code != 200:
            assistant_msg = f"❌ Error: {resp.text}"
        else:
            data = resp.json()
            
            # Format the response nicely
            assistant_msg = data['answer']
            
            # Add SQL query if it was used
            if data.get('sql_query'):
                assistant_msg += f"\n\n**SQL Query:**\n```sql\n{data['sql_query']}\n```"
            
            # Add raw data if available
            if data.get('data'):
                assistant_msg += f"\n\n**Raw Data:**\n```json\n{json.dumps(data['data'], indent=2, default=str)}\n```"
    
    except requests.exceptions.RequestException as e:
        assistant_msg = f"❌ Connection Error: {str(e)}\n\nMake sure the API is running at {API_URL}"
    
    except Exception as e:
        assistant_msg = f"❌ Unexpected Error: {str(e)}"
    
    # Return in Gradio 6.0 format with role/content dictionaries
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": assistant_msg})
    
    return history


with gr.Blocks() as demo:
    gr.Markdown(
        """
        # 🚦 TraffiQ - Traffic Monitoring Chatbot
        Ask questions about your traffic cameras and monitoring data!
        
        **Examples:**
        - How many cameras are in the system?
        - What's the average traffic count?
        - Show me the busiest camera
        - What can you do?
        """
    )

    chatbot = gr.Chatbot(
        label="Chat",
        height=500
    )
    
    with gr.Row():
        msg = gr.Textbox(
            label="Your question",
            placeholder="Ask something about traffic monitoring...",
            scale=4
        )
        submit = gr.Button("Send", scale=1, variant="primary")
    
    clear = gr.Button("Clear Chat")

    # Event handlers
    msg.submit(chat_fn, [msg, chatbot], chatbot).then(
        lambda: "", None, msg  # Clear input after submit
    )
    submit.click(chat_fn, [msg, chatbot], chatbot).then(
        lambda: "", None, msg
    )
    clear.click(lambda: None, None, chatbot)

demo.launch(server_name="0.0.0.0", server_port=7860, theme=gr.themes.Soft())