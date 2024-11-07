import os
import uuid

from server.agent.html_agent import HTMLAgent
from server.constants import LLM_FOLDER_PATH
from server.db import add_message, get_chat_messages
from server.model import LlamaCppWrapper

from pydantic import BaseModel

INFERENCE_TYPE = "llama.cpp"
LLM_PATH = "models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
LLM_MODEL = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"


class DialogManager:
    def __init__(
        self,
        temperature=0.0,
        max_new_tokens=2048,
        max_context_size=15000,
        max_prompt_size=2000,
        repeat_penalty=1.1,
        top_k=30,
        top_p=1.0,
        model_path=LLM_PATH,
        model_name=LLM_MODEL,
    ):
        self.model_path = model_path
        self.model_name = model_name
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.max_prompt_size = max_prompt_size
        self.max_context_size = max_context_size
        self.max_model_input_tokens = (
            max_new_tokens + max_context_size + max_prompt_size
        )
        self.top_k = top_k
        self.top_p = top_p
        self.repeat_penalty = repeat_penalty

        self.llm_client = self.get_llm_client()

        self.agent = HTMLAgent(llm_client=self.llm_client)

    def add_chat_query(
        self,
        chat_id,
        user_query,
        page_content,
        url,
        processing_settings,
        file_type="html",
    ):
        chat_history = get_chat_messages(chat_id=chat_id)

        add_message(
            1,
            chat_id=chat_id,
            url=url,
            file_type=file_type,
            role="user",
            message=user_query,
            model_name="",
            service_comments="",
            version="0.3.1",
        )

        print("\n".join([f"{d.role} - {d.message}" for d in chat_history]))
        print(user_query)
        print(processing_settings)

        if processing_settings.use_page_context:
            bot_response = self.agent.get_relevant_info(
                # dialog_roadmap.user_input_explanation_what_he_want, page_content, url
                user_query,
                chat_history,
                page_content,
                url,
                processing_settings,
            )
        else:
            bot_response = self.agent.generate_chat_response(
                get_chat_messages(chat_id=chat_id)
            )

        # handle bot response and write to db
        complete_response = ""
        for chunk in bot_response:
            complete_response += chunk
            yield chunk

        params = {
            "llm_params": self.agent.client.get_params(),
            "processing_settings": processing_settings.json(),
        }

        add_message(
            1,
            chat_id=chat_id,
            url=url,
            file_type=file_type,
            role="bot",
            message=complete_response,
            model_name=self.model_name,
            service_comments=str(params),
            version="0.3.1",
        )

    def from_chat_to_llm_tempalte(self, dialog_history):
        pass

    def get_chat_id(self):
        return str(uuid.uuid4())

    def get_chat_messages(self, chat_id):
        return [
            {message.role: message.message}
            for message in get_chat_messages(chat_id=chat_id)
        ]

    # TODO:
    def change_dialog_model(self, model_name):
        self.model_path = os.path.join(LLM_FOLDER_PATH, model_name)
        self.llm_client = self.get_inference_client(
            model_path=os.path.join(LLM_FOLDER_PATH, model_name),
            model_name=model_name,
            temperature=0.2,
            max_new_tokens=2048,
        )
        pass

    def get_existed_models(self):
        return os.listdir(LLM_FOLDER_PATH)

    def get_current_model(self):
        return self.model_name

    def get_llm_client(self):
        if INFERENCE_TYPE == "llama.cpp":
            return LlamaCppWrapper(
                model_path=self.model_path,
                temperature=self.temperature,
                repeat_penalty=self.repeat_penalty,
                max_tokens=self.max_model_input_tokens,
                n_ctx=self.max_context_size,
                top_k=self.top_k,
                top_p=self.top_p,
                max_prompt_size=self.max_prompt_size,
            )
        else:
            raise NotImplementedError
