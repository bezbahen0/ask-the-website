from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from constants import LLM_FOLDER_PATH

app = FastAPI()

# Enable CORS
origins = ["*"]  # Replace with your allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_models_from_path(path):
    return []

@app.get("/get_current_model")
async def get_current_model():
    return {"current_model": "model path"}

@app.post("/load_model")
async def load_model():
    return {"status": "Model loaded successfully"}

@app.get("/get_gguf_files")
async def get_gguf_files():
    return {"gguf_files": [LLM_MODEL_PATH]}

@app.post("/query")
async def handle_query():
    return {"response": "response"}

@app.get("/health")
async def health_check():
    try:
        return {"status": "healthy"}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": str(e)}, 500

if __name__ == "__main__":
    print("API endpoint available.")
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)