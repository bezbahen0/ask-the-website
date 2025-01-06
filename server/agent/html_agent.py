from tqdm import tqdm

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

from server.partition import get_processor
from server.partition.html_processor import HTMLProcessingSettings


SYSTEM_PROMPT = """Your task is to answer this question ```{question}``` by finding everything relevant in a complex document obtained after processing a web page in a browser and passed to you in {format} format.
Here is the document:
```{document}```

Also, here is the link, {page_url}, where this document is located.

{additional_processing_markers}

First, reflect on the main topic of the document, key sections and their relationships.
Find information in the context that directly answers the question.
Identify related information that may complement the answer.
Evaluate if there is sufficient information for a complete answer.
Indicate where information may be incomplete or needs clarification.
At the end, provide all relevant information.
"""

CHUNK_PROCESSING_PROMPT = """Your task is to answer this question ```{question}``` by finding everything relevant in a portion of a complex document obtained after processing a web page in a browser and passed to you in {format} format.
Here is the document portion:
```{document}```

Also, here is the link, {page_url}, where this document is located.

{additional_processing_markers}

First, reflect on the main topic of this document portion, key sections and their relationships.
It is also important to indicate what layout of the web page this part can be.
Find information in the context that directly answers the question.
Identify related information that may complement the answer.
Evaluate if there is sufficient information for a complete answer.
Indicate where information may be incomplete or needs clarification.
At the end, provide all information and an overall assessment of the document's relevance to answering the question.
"""

CHUNK_AGREGATION_PROMPT = """Your task is to combine scattered responses from one document that was processed part by part, from top to bottom.
Consequently, all responses from different parts are in the order they were processed.

Reflect on what you have at hand and what needs to be done.
Create a text that would combine all these responses into one comprehensive answer.

Don't add anything on your own, use only information from the responses.

Here are all the responses in the order they were processed:
```{documents}```
"""


class AnswerGeneratorWithRelevanceScore(BaseModel):
    reflection: str
    relevant_information: str
    relevant_information_relevance_score_to_question: float = Field(
        default=None, description="Relevance to the question (0-1)"
    )


# confidence": "Уровень уверенности в релевантности"


class AnswerGenerator(BaseModel):
    reflection: str
    relevant_information: str


class HTMLAgent:
    def __init__(
        self,
        llm_client,
    ):
        self.client = llm_client

        self.content_processor = get_processor()

    def get_relevant_info(self, question, context, url, processing_settings):
        processing_settings = HTMLProcessingSettings(**processing_settings)

        print(f"page_url: {url}")

        self.content_processor = get_processor(page_type="text/html")

        is_full_page = self.content_processor.is_full_page(context)

        document = self.content_processor.process_page(
            context,
            url,
            split=False,
            processing_settings=processing_settings,
            context_len_checker=self.client.check_context_len,
        )

        if not self.client.check_context_len(text=document):
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
                additional_processing_markers = f"""{i} part of the webpage, the webpage is divided into {len(documents)} parts in total"""

                messages = [
                    {
                        "role": "user",
                        "content": CHUNK_PROCESSING_PROMPT.format(
                            question=question,
                            format=(
                                "markdown"
                                if processing_settings.use_only_text
                                else "html"
                            ),
                            document=doc,
                            page_url=url,
                            additional_processing_markers=additional_processing_markers,
                        ),
                    },
                ]

                response = self.client.generate(
                    messages,
                    stream=False,
                )
                print(response)
                relevant_chunks.append(response)

            print(relevant_chunks)
            messages = [
                {
                    "role": "user",
                    "content": CHUNK_AGREGATION_PROMPT.format(
                        documents=self.content_processor.make_page(
                            documents, relevant_chunks, processing_settings
                        ),
                    ),
                },
            ]
            response_from_model = self.client.generate(
                messages,
                stream=False,
            )
        else:
            print("\n\nSINGLE RUN\n\n")

            additional_processing_markers = """"""

            messages = [
                {
                    "role": "user",
                    "content": SYSTEM_PROMPT.format(
                        question=question,
                        format=(
                            "markdown" if processing_settings.use_only_text else "html"
                        ),
                        document=document,
                        page_url=url,
                        additional_processing_markers=additional_processing_markers,
                    ),
                },
            ]
            response_from_model = self.client.generate(
                messages,
                stream=False,
            )
        print("\n\n----------Response from model----------------\n\n")
        print(response_from_model)
        return response_from_model
