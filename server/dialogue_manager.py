import os
import uuid

from server.agent.html_agent import HTMLAgent
from server.constants import LLM_FOLDER_PATH
from server.db import add_message, get_chat_messages


class DialogManager:
    def __init__(self):
        self.agent = HTMLAgent(temperature=0.2, max_new_tokens=2048)

    def add_chat_query(self, chat_id, user_query, page_content, url, file_type="html"):
        add_message(
            1,
            chat_id=chat_id,
            url=url,
            file_type=file_type,
            role="user",
            message=user_query,
            model_name='',
            service_comments='',
            version="0.2.6",
        )

        print([message.message for message in get_chat_messages(chat_id=chat_id)])

        response_from_model = self.agent.question_answer_with_context(
            user_query, page_content, url
        )
        
        # handle bot response and write to db
        complete_response = ""
        for chunk in response_from_model:
            complete_response += chunk
            yield chunk  

        add_message(
            1,
            chat_id=chat_id,
            url=url,
            file_type=file_type,
            role="bot",
            message=complete_response,
            model_name=self.agent.model_name,
            service_comments=f'{self.agent.client.get_params()}',
            version="0.2.6",
        )

    def get_chat_id(self):
        return str(uuid.uuid4())

    def change_dialog_model(self, model_name):
        self.agent = HTMLAgent(
            model_path=os.path.join(LLM_FOLDER_PATH, model_name),
            model_name=model_name,
            temperature=0.2,
            max_new_tokens=2048,
        )

    def get_existed_models(self):
        return os.listdir(LLM_FOLDER_PATH)

    def get_current_model(self):
        return self.agent.model_name
