from server.partition import get_processor
from tqdm import tqdm

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

SYSTEM_PROMPT = """Твоя задача быть ассистен для помощи мне в работе над страницами в браузере которые я вижу и тебе буду предоставлять, я буду упоминать тебе о том на какой странице я сейчас нахожусь, и давать тебе процитированные тэги и пояснения к ним, Ты можешь давать ответ только по одной странице за раз, если тебе нужно еще раз увидеть прошлую странице чтобы дать ответ, скажи мне об этом. Если ты не видишь Контент страницы или Нет релевантной информации к вопросу на Станице, то похоже что вопрос не требует контекста и просто веди со мной диалог"""


class HtmlRetrievalFormat(BaseModel):
    is_user_query_required_visual_elements_or_functional: Literal[
        "visual elements", "functional elements of the web page"
    ]
    the_user_query_implies_a_search_of_the_main_content_of_the_page: bool
    are_tag_attributes_required_to_answer_the_user_query: Literal[
        "to answer user query need tag attributes", "tag attributes are not needed"
    ]


#class HTMLProcessorConfig(BaseModel):
#   chain_of_thougs: str
#   links: bool
#   tables: bool
#   navigation: bool
#   script: bool
#   header: bool
#   style: bool
#   svg: bool
#   tag_attributes: bool
#   

class HTMLAgent:
    def __init__(
        self,
        llm_client,
        system_prompt=SYSTEM_PROMPT,
    ):
        self.system_prompt = system_prompt
        self.client = llm_client

        self.content_processor = get_processor()

    def get_relevant_info(self, question, dialog_history, context, url):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [
            {
                "role": "user" if conv.role == "user" else "assistant",
                "content": conv.message,
            }
            for conv in dialog_history
        ]

        retrieval_request = messages + [
            {
                "role": "user",
                "content": f"I need you to think about my user query and give your decision on what needs to be done. User query ```{question}```",
            },
        ]

        response = self.client.generate(
            retrieval_request, schema=HtmlRetrievalFormat.model_json_schema(), stream=False
        )
        html_processor_config = HtmlRetrievalFormat.model_validate_json(response)
        print("\n\n RESPONSE \n\n")
        print(response)

        print(f"page_url: {url}")

        tag_attributes = (
            False
            if html_processor_config.are_tag_attributes_required_to_answer_the_user_query
            == "tag attributes are not needed"
            else True
        )
        only_visual_tags = True

        self.content_processor = get_processor(page_type="html")
        documents, page_meta = self.content_processor.process_page(
            context,
            url,
            tag_attributes=tag_attributes,
            only_visual_tags=only_visual_tags,
            context_len_checker=self.client.check_context_len
        )

        if not self.client.check_context_len(text=str(documents)):
            documents, page_meta = self.content_processor.process_page(
                context,
                url,
                split_to_chunks=True,
                context_len_checker=self.client.check_context_len,
            )
            print(f"Find {len(documents)} chunks")

            relevant_chunks = []
            for index, doc in tqdm(enumerate(documents)):
                message_parting = messages
                if self.client.check_context_len(doc):

                    messages_parting = messages + [
                        # {"role": "system", "content": CITATION_SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": f"{question} \n\n Part of web page \n\n ```{doc}```",
                        },
                    ]
                    response = self.client.generate(
                        messages, stream=False
                    )
                    print("\n\n RESPONSE \n\n")
                    print(response)
                    print("\n\n docs \n\n")
                    print(doc)
                    relevant_chunks.append(response)
                    
            messages = [
                # {"role": "system", "content": CITATION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Составь единый ответы из нескольких User query: ```{question}``` \n\n Ответы по разным частям одно web страницы: ```{relevant_chunks}```",
                },
            ]
            response_from_model = self.client.generate(
                messages, stream=True
            )
                    
            response_from_model = relevant_chunks
        else:
            print("\n\nGOOOODYYYY\n\n")
            messages += [
                # {"role": "system", "content": CITATION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"{question} \n\n Web page \n\n ```{str(documents)}```",
                },
            ]
            response_from_model = self.client.generate(
                messages, stream=True
            )

            print("\n\n RESPONSE \n\n")
            print(response_from_model)
            print("\n\n docs \n\n")
            print(documents)

        return response_from_model

    def generate_chat_response(self, dialog_history, relevant_chunks_responses):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for conv in dialog_history:
            if conv.role == "user":
                messages.append({"role": "user", "content": conv.message})
            else:
                messages.append({"role": "assistant", "content": conv.message})

        return self.client.generate(messages, stream=True)
