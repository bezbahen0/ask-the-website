import os

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from server.dialogue_manager import DialogManager
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


dialogue_manager = DialogManager()


class Model(BaseModel):
    model: str


class Chat(BaseModel):
    chat_id: str


class PageContentProcessingSettings(BaseModel):
    use_page_context: bool
    content_type: str
    processing_settings: dict


class Query(BaseModel):
    chat_id: str
    query: str
    page_content: str
    page_url: str
    processing_settings: PageContentProcessingSettings


@app.get("/get_chat_id")
async def get_new_chat_id():
    return {"new_chat_id" : dialogue_manager.get_chat_id()}


@app.post("/get_chat_messages")
async def get_chat_messages(chat: Chat):
    print(chat.chat_id)
    return {"dialog": dialogue_manager.get_chat_messages(chat_id=chat.chat_id)}


@app.get("/get_current_model")
async def get_current_model():
    return {"current_model": dialogue_manager.get_current_model()}


@app.post("/load_model")
async def load_model(model: Model):
    print(model)

    dialogue_manager.change_dialog_model(model_name=model.model)

    return {"status": "Model loaded successfully"}


@app.get("/get_gguf_files")
async def get_gguf_files():
    return {"gguf_files": dialogue_manager.get_existed_models()}


@app.post("/query")
async def handle_query(query: Query):
    response_from_model = dialogue_manager.add_chat_query(
        query.chat_id,
        query.query,
        query.page_content,
        query.page_url,
        query.processing_settings,
    )
    return StreamingResponse(response_from_model, media_type="text/plain")


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

    uvicorn.run(app, host="127.0.0.1", port=8080, reload=True)
