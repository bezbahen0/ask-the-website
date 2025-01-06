import os
import uuid

from server.agent import get_agent
from server.constants import LLM_FOLDER_PATH

from server.db import add_message, get_chat_messages

from server.model import LlamaCppWrapper
from server.model import JsonFieldStreamProcessor

from pydantic import BaseModel

INFERENCE_TYPE = "llama.cpp"
LLM_PATH = "models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
LLM_MODEL = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"


SYSTEM_PROMPT = """You are an intelligent browser assistant called Lam, that helps users analyze and work with content from the currently active browser tab. 

You will be given already analyzed results for the page on the active tab from the Q/A system, which will process and highlight relevant information from the page.

Your main tasks are:

1. Reflect on the information you have and what answers you will give to the question
2. Understand and process content only from the current active tab (HTML, PDF, plain text)
3. Provide relevant information and answers based on the given context
4. Help users find specific information within the current page
5. Generate summaries, explanations, or analyses as requested

Important rules:
- Always respond in the same language the user's question is asked in
- Base your answers strictly on the provided context from the current tab
- If information needed is on another page, politely ask the user to navigate to that page first
- If something is unclear or missing from the context, acknowledge this
- Keep responses clear, concise, and well-structured
- When appropriate, use formatting (bullet points, paragraphs) for better readability
- Never make assumptions about content that isn't visible in the current tab
- If user asks about information from another page, remind them that you can only work with the current tab's content"""


REWRITE_PROMPT = """There is a dialogue history with two acting roles user and bot: {dialog}.

User sees a browser page about which bot responds.
Be careful, the dialogue may be about different sites (browser pages), keep track of which iteration on which page the question is asked.

Your task is to use all information from the dialogue to identify a specific question that the user has in their last message, supplementing it with all necessary terms that appear in the dialogue to increase the completeness of the question.


First reflect on what's happening in the dialogue and what needs to be done.

If the dialogue is too short and you can't formulate a question, leave the question in its original form.

If you can't rephrase the question and it's already complete enough, leave it in its original form.

Don't make things up, use only what's in the dialogue and don't add anything on your own.

Your response will be in this format:
{response_format}
"""


class RewriteQuestion(BaseModel):
    reflection: str
    specific_question: str


class AnswerGenerator(BaseModel):
    reflectoin: str
    answer: str


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
        self.answer_processor = JsonFieldStreamProcessor(field_name="answer")

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
            version="0.3.6.4",
        )

        chat_history = get_chat_messages(chat_id=chat_id)

        print("\n".join([f"{d.role} - {d.message}." for d in chat_history]))
        print(user_query)
        print(processing_settings)

        if processing_settings.use_page_context or not processing_settings.content_type:

            if len(chat_history) > 1:
                user_query = self.get_specific_question_from_user(
                    "\n\n".join([f"Active browser tab: {d.url}\n {d.role}: ```{d.message}```" for d in chat_history])
                )

            agent_relevant_info = agent.get_relevant_info(
                user_query,
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
            version="0.3.6.4",
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
                "content": f"{conv.message}.\nCurrent active tab: {conv.url}",
            }
            for conv in dialog_history
        ]
        if context:
            messages[-1]["content"] = messages[-1]["content"] + f"\n Context: \n```{context}```"

        return self.llm_client.generate(
            messages,
            stream=True,
            #stream_processor=self.answer_processor,
            #schema=AnswerGenerator.model_json_schema(),
        )

    def get_specific_question_from_user(self, dialog_history):
        response = self.llm_client.generate(
            [
                {
                    "role": "user",
                    "content": REWRITE_PROMPT.format(
                        dialog="Start of dialogue\n\n" + dialog_history,
                        response_format=RewriteQuestion.model_json_schema(),
                    ),
                }
            ],
            schema=RewriteQuestion.model_json_schema(),
            stream=False,
        )
        print(dialog_history)
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
