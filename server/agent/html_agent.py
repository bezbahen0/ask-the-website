from tqdm import tqdm

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

from server.partition import get_processor
from server.partition.html_processor import HTMLProcessingSettings
from server.model import JsonFieldStreamProcessor


SYSTEM_PROMPT = """Твоя задача отвечая на этот вопрос ```{question}```, находить в сложном документе полученном после обработки web страницы в браузере и переданном тебе в {format} формате, всю что ты найдешь для ответа на этот вопрос.
Вот документ:
```{document}```

Так же вот ссылка, {page_url}, по которой этот документ находится.

{additional_processing_markers}

Сначала поразмышляй над основной темой документа, ключевым разделам и их взаимосвязями.
Найди в контексте информацию, напрямую отвечающую на вопрос.
Определи связанную информацию, которая может дополнить ответ.
Оцени достаточность информации для полного ответа.
Укажи, где информация может быть неполной или требует уточнения.
В конце выдай всю релевантную информацию.

Формат твоего ответа будет в таком виде:
{response_format}
"""

CHUNK_PROCESSING_PROMPT = """Твоя задача отвечая на этот вопрос ```{question}```, находить в куске одного сложного документа полученном после обработки web страницы в браузере и переданном тебе в {format} формате, всю что ты найдешь для ответа на этот вопрос.
Вот кусок документа:
```{document}```

Так же вот ссылка, {page_url}, по которой этот документ находится.

{additional_processing_markers}

Сначала поразмышляй над основной темой куска документа, ключевым разделам и их взаимосвязями.
Найди в контексте информацию, напрямую отвечающую на вопрос.
Определи связанную информацию, которая может дополнить ответ.
Оцени достаточность информации для полного ответа.
Укажи, где информация может быть неполной или требует уточнения.
В конце выдай всю информацию и общую оценку релевантности документа для ответа на вопрос.

Формат твоего ответа будет в таком виде:
{response_format}
"""

CHUNK_AGREGATION_PROMPT = """Твоя задача объединить разрозненный ответы одного документа, документ обрабатывался часть за частью, сверху в низ.
Следовательно, все ответы по разным частям идут в порядке того как они обрабатывались. 

Поразмышляй над тем что у тебя на руках и что нужно сделать.
Сформируй текст который бы объединил все эти ответы в один ответ.

Не добавляй от себя ничего, используй только информацию из ответов.

Вот все ответы в порядке того как они обрабатывались:
```{documents}```

Формат твоего ответа будет в таком виде:
{response_format}
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
        self.answer_processor = JsonFieldStreamProcessor(field_name="answer")

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
        #print(document)

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
                            response_format=AnswerGeneratorWithRelevanceScore.model_json_schema(),
                        ),
                    },
                ]

                response = self.client.generate(
                    messages,
                    stream=False,
                    schema=AnswerGeneratorWithRelevanceScore.model_json_schema(),
                )
                print(response)
                #print(doc)
                relevant_chunks.append(response)
            print(relevant_chunks)
            messages = [
                {
                    "role": "user",
                    "content": CHUNK_AGREGATION_PROMPT.format(
                        documents=self.content_processor.make_page(
                            documents, relevant_chunks, processing_settings
                        ),
                        response_format=AnswerGenerator.model_json_schema(),
                    ),
                },
            ]
            response_from_model = self.client.generate(
                messages,
                stream=False,
                schema=AnswerGenerator.model_json_schema(),
            )
        else:
            print("\n\nSINGLE RUN\n\n")
            #print(document)

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
                        response_format=AnswerGenerator.model_json_schema(),
                    ),
                },
            ]
            response_from_model = self.client.generate(
                messages,
                stream=False,
                schema=AnswerGenerator.model_json_schema(),
            )
        print("\n\n----------Response from model----------------\n\n")
        print(response_from_model)
        return response_from_model
