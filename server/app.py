import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from server.constants import LLM_FOLDER_PATH
from server.model import LLMClientAdapter

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


llm_model = LLMClientAdapter(temperature=0.4, max_new_tokens=512)


@app.get("/get_current_model")
async def get_current_model():
    return {"current_model": llm_model.model_name}


@app.post("/load_model")
async def load_model(model: dict):
    global llm_model
    print(model)

    llm_model = LLMClientAdapter(
        model_path=os.path.join(LLM_FOLDER_PATH, model["model"]),
        model_name=model["model"],
        temperature=0.4,
        max_new_tokens=512,
    )
    
    return {"status": "Model loaded successfully"}


@app.get("/get_gguf_files")
async def get_gguf_files():
    return {"gguf_files": os.listdir(LLM_FOLDER_PATH)}


@app.post("/query")
async def handle_query(query: dict):
    response_from_model = llm_model.generate(question=query["query"])
    print(response_from_model)
    return {"response": response_from_model}


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
