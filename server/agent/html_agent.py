from tqdm import tqdm

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

from server.partition import get_processor
from server.partition.html_processor import HTMLProcessingSettings


SYSTEM_PROMPT = """Твоя задача быть ассистентом для помощи мне в работе над документами в формате html в браузере, который я вижу, я буду упоминать тебя о том, на какой странице я сейчас нахожусь, это как дополнительная информация тебе, а также передать контекстный документ в формате html.

HTML-контент может быть сложным, там могут быть блокирующие факторы в виде графических меню, рекламных материалов, старайся найти необходимую мне информацию среди всего этого и сам по себе, рассуждая над тем, что из информации в формате html тебе понадобится.

Ты можешь дать ответ только на одной странице за раз, если тебе нужно еще раз увидеть прошлую страницу, чтобы дать ответ, скажи мне об этом."""


class HTMLAgent:
    def __init__(
        self,
        llm_client,
        system_prompt=SYSTEM_PROMPT,
    ):
        self.system_prompt = system_prompt
        self.client = llm_client

        self.content_processor = get_processor()

    def get_relevant_info(
        self, question, dialog_history, context, url, processing_settings
    ):
        processing_settings = HTMLProcessingSettings(**processing_settings)

        messages = [
            {
                "role": "user" if conv.role == "user" else "assistant",
                "content": conv.message,
            }
            for conv in dialog_history
        ]

        print(f"page_url: {url}")

        self.content_processor = get_processor(page_type="text/html")
        documents = self.content_processor.process_page(
            context,
            url,
            split=False,
            processing_settings=processing_settings,
            context_len_checker=self.client.check_context_len,
        )

        if not self.client.check_context_len(text=str(documents)):
            documents = self.content_processor.process_page(
                context,
                url,
                split=True,
                processing_settings=processing_settings,
                context_len_checker=self.client.check_context_len,
            )
            print(f"Find {len(documents)} chunks")
            print(
                [self.client.check_context_len(d, return_len=True) for d in documents]
            )
            relevant_chunks = []
            for i, doc in tqdm(enumerate(documents), total=len(documents)):
                doc = self.content_processor.make_page(documents, i, relevant_chunks, processing_settings)
                messages_parting = messages + [
                    {
                        "role": "user",
                        "content": f"{question} Не повторяй информацию что была в прошлых ответах, они помеченны ты увидишь \n\n Page Url: ```{url}``` \n\nPart of web page \n\n ```{doc}```",
                    },
                ]

                response = self.client.generate(messages_parting, stream=False)
                relevant_chunks.append(response)
                print(doc)
            messages = messages + [
                {
                    "role": "user",
                    "content": f"Составь единый ответы из нескольких User query: ```{question}``` \n\n Ответы по разным частям одной web страницы: ```{self.content_processor.make_page(documents, len(documents)-1, relevant_chunks, processing_settings)}```",
                },
            ]
            response_from_model = self.client.generate(messages, stream=True)
        else:
            print("\n\nGOOOODYYYY\n\n")
            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
            messages += [
                # {"role": "system", "content": CITATION_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"{question} \n\n Page url: ```{url}```\n\n Web page \n\n ```{str(documents)}```",
                },
            ]
            response_from_model = self.client.generate(messages, stream=True)
        return response_from_model

    def generate_chat_response(self, dialog_history):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for conv in dialog_history:
            if conv.role == "user":
                messages.append({"role": "user", "content": conv.message})
            else:
                messages.append({"role": "assistant", "content": conv.message})

        return self.client.generate(messages, stream=True)
