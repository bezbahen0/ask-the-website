from tqdm import tqdm

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

from server.partition import get_processor
from server.partition.html_processor import HTMLProcessingSettings
from server.model import JsonFieldStreamProcessor

SYSTEM_PROMPT = """You are an intelligent browser assistant that helps users analyze and work with content from the currently active browser tab. Your main tasks are:

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
- If user asks about information from another page, remind them that you can only work with the current tab's content
"""


CHUNK_PROCESSING_PROMPT = """You are processing a part of a webpage. Your task is to:

1. Reflect on the information you have and what answers you will give to the question
2. Extract only relevant information from this chunk that relates to the user's question
3. Provide a focused, self-contained response about this specific part
4. Consider previous findings when analyzing new information
5. Keep the response concise and factual
6. Format the response so it can be easily combined with other parts

Remember:
- This is part of an iterative analysis process
- Focus on new relevant information in this chunk
- Avoid repeating information already found in previous parts
- Always respond in the same language the user's question is asked in
- Maintain the user's original language in the response
- If you find information that complements or contradicts previous findings, note this

The final response will be assembled from multiple parts, so keep your answer focused and relevant to this specific chunk.
"""


class AnswerGeneratorWithRelevanceScore(BaseModel):
    reflections: str
    answer: str
    answer_relevance_score_to_question: float = Field(
        default=None, description="Relevance to the question (0-1)"
    )


class AnswerGenerator(BaseModel):
    reflections: str
    answer: str


class HTMLAgent:
    def __init__(
        self,
        llm_client,
        system_prompt=SYSTEM_PROMPT,
    ):
        self.system_prompt = system_prompt
        self.client = llm_client

        self.content_processor = get_processor()
        self.answer_processor = JsonFieldStreamProcessor(field_name="answer")

    def get_relevant_info(
        self, question, dialog_history, context, url, processing_settings
    ):
        processing_settings = HTMLProcessingSettings(**processing_settings)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [
            {
                "role": "user" if conv.role == "user" else "assistant",
                "content": f"{conv.message} Page Url: ```{conv.url}```",
            }
            for conv in dialog_history
        ]

        print(f"page_url: {url}")

        self.content_processor = get_processor(page_type="text/html")

        is_full_page = self.content_processor.is_full_page(context)
        print(is_full_page)
        selected_content = (
            "Full web page"
            if is_full_page
            else "This is not the entire web page, it is the selected content on the page"
        )

        documents = self.content_processor.process_page(
            context,
            url,
            split=False,
            processing_settings=processing_settings,
            context_len_checker=self.client.check_context_len,
        )
        print(documents)

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
                doc = f"""{i} part of the webpage, the webpage is divided into {len(documents)} parts in total\n```{doc}```\n"""

                messages_parting = [
                    {"role": "system", "content": CHUNK_PROCESSING_PROMPT}
                ]
                messages_parting += messages[1:]
                messages_parting += [
                    {
                        "role": "user",
                        "content": f"{question} \n\n Page Url: ```{url}``` \n\nPart of web page \n\n {doc} \n\n"
                        + f"Your response format: {AnswerGeneratorWithRelevanceScore.model_json_schema()}",
                    },
                ]

                response = self.client.generate(
                    messages_parting,
                    stream=False,
                    schema=AnswerGeneratorWithRelevanceScore.model_json_schema(),
                )
                print(response)
                print(doc)
                relevant_chunks.append(response)

            messages += [
                {
                    "role": "user",
                    "content": f"My question: {question} \n\n   {selected_content}. The content has already been submitted part by part here are the answers to my question in parts with reflection: \n\n```{self.content_processor.make_page(documents, relevant_chunks, processing_settings)}```",
                },
            ]
            response_from_model = self.client.generate(
                messages,
                stream=True,
                schema=AnswerGenerator.model_json_schema(),
                stream_processor=self.answer_processor,
            )
        else:
            print("\n\nSINGLE RUN\n\n")
            print(str(documents))

            messages += [
                {
                    "role": "user",
                    "content": f"Question: {question} \n\n Page url: ```{url}```\n\n {selected_content} \n\n ```{str(documents)}```"
                    + f"\nYour response format: {AnswerGenerator.model_json_schema()}",
                },
            ]
            response_from_model = self.client.generate(
                messages,
                stream=True,
                schema=AnswerGenerator.model_json_schema(),
                stream_processor=self.answer_processor,
            )
        return response_from_model

    def generate_chat_response(self, dialog_history):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [
            {
                "role": "user" if conv.role == "user" else "assistant",
                "content": f"{conv.message} Page Url: ```{conv.url}```",
            }
            for conv in dialog_history
        ]
        return self.client.generate(messages, stream=True)
