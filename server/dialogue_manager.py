import os
import uuid

from server.agent import get_agent
from server.constants import LLM_FOLDER_PATH
from server.db import add_message, get_chat_messages
from server.model import LlamaCppWrapper

from pydantic import BaseModel

INFERENCE_TYPE = "llama.cpp"
LLM_PATH = "models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
LLM_MODEL = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"


SYSTEM_PROMPT = """На основе предоставленной информации и вопросов

Сформируй ответ, который:
1. Точно отвечает на поставленный вопрос
2. Использует только факты из контекста
3. Структурирован и логичен
4. Написан на языке который использует вопрос

Решай неопределенности (если они есть)

Правила формирования ответа:
- Начни с прямого ответа на вопрос
- Добавь контекст только если он существенен
"""

REWRITE_PROMPT = """Есть история диалога с двумя действующими ролями user и bot: {dialog}.

User видит страницу браузера по контексту которой отвечает bot.

Твоя задача используя всю информацию из диалога выделить конкретизированный вопрос который есть у user в последнем его сообщении дополнив его всеми необходимыми терминами которые встречаются в диалоге для повышения полноты вопроса.

Поразмышляй сначала над тем что происходит в диалоге и что надо делать.

Если диалог слишком маленький и не можешь сформулировать вопрос то оставь вопрос в исходном виде.

Если не можешь перефразировать вопрос и он и так достаточно полный то оставь его в исходном виде.

Не ври, используй только то что есть в диалоге от себя ничегон не добавляй.

Формат твоего ответа будет в таком виде:
{response_format}
"""


class RewriteQuestion(BaseModel):
    reflection: str
    specific_question: str


class DialogManager:
    def __init__(
        self,
        temperature=0.3,
        max_new_tokens=4048,
        max_context_size=15000,
        max_prompt_size=3000,
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

    def add_chat_query(
        self,
        chat_id,
        user_query,
        page_content,
        url,
        processing_settings,
    ):
        agent = get_agent(processing_settings.content_type)(self.llm_client)

        add_message(
            1,
            chat_id=chat_id,
            url=url,
            file_type=processing_settings.content_type,
            role="user",
            message=user_query,
            model_name="",
            service_comments=str(processing_settings.json()),
            version="0.3.6.3",
        )

        chat_history = get_chat_messages(chat_id=chat_id)

        print("\n".join([f"{d.role} - {d.message}." for d in chat_history]))
        print(user_query)
        print(processing_settings)

        if processing_settings.use_page_context or not processing_settings.content_type:

            specific_user_query = self.get_specific_question_from_user(
                "\n".join([f"{d.role} - {d.message}" for d in chat_history])
            )

            agent_relevant_info = agent.get_relevant_info(
                specific_user_query,
                page_content,
                url,
                processing_settings.processing_settings,
            )
            bot_response = self.generate_chat_response(
                chat_history, agent_relevant_info
            )
        else:
            bot_response = self.generate_chat_response(chat_history)

        # handle bot response and write to db
        complete_response = ""
        for chunk in bot_response:
            complete_response += chunk
            yield chunk

        params = {
            "llm_params": agent.client.get_params(),
            "processing_settings": processing_settings.json(),
        }

        add_message(
            1,
            chat_id=chat_id,
            url=url,
            file_type=processing_settings.content_type,
            role="bot",
            message=complete_response,
            model_name=self.model_name,
            service_comments=str(params),
            version="0.3.6.3",
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

    def generate_chat_response(self, dialog_history, context=None):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [
            {
                "role": "user" if conv.role == "user" else "assistant",
                "content": f"{conv.message} {'' if not context else 'Контекст:' + context}",
            }
            for conv in dialog_history
        ]
        return self.llm_client.generate(messages, stream=True)

    def get_specific_question_from_user(self, dialog_history):
        response = self.llm_client.generate(
            [
                {
                    "role": "user",
                    "content": REWRITE_PROMPT.format(
                        dialog="Начало диалога\n\n" + dialog_history,
                        response_format=RewriteQuestion.model_json_schema(),
                    ),
                }
            ],
            schema=RewriteQuestion.model_json_schema(),
            stream=False,
        )
        print("\n\n REWRITED ------------------------------------\n\n")
        print(response)
        response = RewriteQuestion.model_validate_json(response)
        return response.specific_question

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
