import os
import json
import traceback
from fastapi import FastAPI


from typing import List


app = FastAPI()


@app.post("/set_selected_folder")
async def set_selected_folder():
    global selected_folder
    try:
        data = request.get_json()
        selected_folder = data.get("selectedFolder", "")
        print(f"Selected folder path: {selected_folder}")
        return jsonify({"status": "Folder path set successfully"})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.get("/get_selected_folder")
async def get_selected_folder():
    global selected_folder
    try:
        return jsonify({"selectedFolder": selected_folder})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.get("/get_current_model")
async def get_current_model():
    try:
        return jsonify({"current_model": model_path})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.post("/load_model")
async def load_model():
    try:
        data = request.get_json()
        print(f"Loading model: {data}")
        model_path_file = os.path.dirname(model_path)
        print(f"Loading model: {model_path_file}")
        print(f"Loading model: {data}")
        model_path_new = os.path.join(model_path_file, data.get("model", ""))
        bot = LLMChatBot(model_path=model_path_new)
        return jsonify({"status": "Model loaded successfully"})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Route to get the list of .gguf files in the model directory
@app.get("/get_gguf_files")
async def get_gguf_files():
    try:
        gguf_files = []
        if model_path:
            # remove the file name from the path
            model_path_file = os.path.dirname(model_path)
            for file in os.listdir(model_path_file):
                if file.endswith(".gguf"):
                    gguf_files.append(file)
        return jsonify({"gguf_files": gguf_files})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.post("/query")
async def handle_query():
    try:
        data = request.get_json()
        user_message = data.get("query", "")
        print(f"Received query: {user_message}")
        response = bot.get_response(user_message)
        print(f"Sending response: {response}")
        return jsonify({"response": response})
    except Exception as e:
        # print(f'Error: {str(e)}')
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.get("/health")
async def health_check():
    try:
        return jsonify({"status": "healthy"})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
