from server.model import LlamaCppWrapper
from server.partition import get_processor
from tqdm import tqdm


LLM_PATH = "models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
LLM_MODEL = "Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
INFERENCE_TYPE = "llama.cpp"
PROMPT_TEMPLATE_END_OF_TURN = """<|im_end|>"""
PROMPT_TEMPLATE_START_OF_TURN = """<|im_start|>"""


SYSTEM_PROMPT = """Твоя задача быть ассистен для помощи мне в работе над статьями и любой информации, если ты не знаешь ответ скажи что не знаешь, если статья написана не на русском выдавай ответ на русском, не переводя технические термины, тебе будет предоставленн контекст статьи с ссылками, текстовой информацией в разрозненном виде, твоя задача помогать мне с любыми запросами что я тебя попрошу сделать с контекстом в виде статьи, которой ты получишь."""

AGGREGATE_SYSTEM_PROMPT = """Твоя роль это ассистен для помощи мне в работе над статьями и любой информации. 

Каждую ответ рассматривай как часть общей мозаики. Если какой-то чанк содержит ключевую информацию, которая может помочь ответить на вопрос, используй её в ответе. Если разные ответы дополняют друг друга, объединяй их логично и последовательно. Если в ответах есть противоречия, постарайся учесть их и предложить наиболее вероятный ответ.

Важно: Интегрируй информацию из всех релевантных ответов таким образом, чтобы конечный ответ был полным, точным и содержал всю необходимую информацию для ответа на вопрос.

Если информации недостаточно для окончательного ответа, укажи это
"""


REWRITE_SYSTEM_PROMPT = """Твоя задача обрабатывать пользовательский вопрос и решать эллиптические фразы, т.е. дополнять существующий эллиптрический ,пользовательский, вопрос и давать мне его развернутый вид, по типу 
user: какая погада сегодня 
bot: +19 солнечно, 
user: а на заватра? 

Результатом является - какая погда завтра?.
Убери лишний текст и оставь только развернутый текст вопроса.
Исправь стилистические и синтаксические ошибки.
Приведи только итоговый текст без предисловий."""


SUMARIZE_SYSTEM_PROMPT = """Твоя задача анализировать приведенную часть документа и цитировать  из него только информацию относящуюся к основному вопросу, Цитируй без дублирования информации. Если в части документа нет информации котороую можно было бы процитировать напиши **Кусок документа не релевантен**, без объяснения почему он не релевантен."""


class HTMLAgent:
    def __init__(
        self,
        temperature,
        max_new_tokens,
        max_context_size=16000,
        max_prompt_size=3000,
        repeat_penalty=1.1,
        top_k=30,
        top_p=1.0,
        model_path=LLM_PATH,
        model_name=LLM_MODEL,
        system_prompt=SYSTEM_PROMPT,
    ):
        self.model_path = model_path
        self.model_name = model_name
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens
        self.max_prompt_size = max_prompt_size
        self.max_context_size = max_context_size
        self.top_k = top_k
        self.top_p = top_p
        self.system_prompt = system_prompt
        self.client = self.get_inference_client(
            temperature,
            repeat_penalty,
            top_k,
            top_p,
            max_new_tokens,
            max_context_size,
            max_prompt_size,
        )
        # self.vector_processor = Vectorizer()
        self.content_processor = get_processor()

    def rewrite_question_with_context(self, question, dialog_history):
        response = self.generate(
            question=question,
            context="\n".join([f"{d.role}: {d.message}" for d in dialog_history]),
            system_prompt=REWRITE_SYSTEM_PROMPT,
            stream=False,
        )
        return response

    def get_relevant_info(self, question, context, url):

        print(f"page_url: {url}")
        self.content_processor = get_processor(page_type="html")
        documents, page_meta = self.content_processor.process_page(
            context, url, split_to_chunks=False
        )
        # print(page_meta)

        if not self.client.check_context_len(text="\n".join(documents)):
            documents, page_meta = self.content_processor.process_page(
                context,
                url,
                split_to_chunks=True,
                context_len_checker=self.client.check_context_len,
            )
            print(f"Find {len(documents)} chunks")

            relevant_chunks = []
            for index, doc in tqdm(enumerate(documents)):
                if self.client.check_context_len(doc):
                    if page_meta:
                        context = (
                            f"Это кусок документа:\n url: {url} \n document meta: {page_meta} \nПорядок этого куска документа по отношению ко всему документу: 0..{index}"
                            + doc
                        )
                    else:
                        context = (
                            f"Порядок документа: {index} из {len(documents)} документов:\n url: {url} \n"
                            + doc
                        )

                    response = self.generate(
                        question=question,
                        context=context,
                        system_prompt=SUMARIZE_SYSTEM_PROMPT,
                        stream=False,
                    )
                    print("\n\n--------------------------\n\n")
                    print("\n\nCHUNK: \n\n")
                    print(doc)
                    print("\n\nRESPONSE: \n\n")
                    print(response)
                    print("\n\n--------------------------\n\n")
                    relevant_chunks.append(response)

            # print([len(self.client.tokenize(text)) for text in relevant_chunks])
            # print(relevant_chunks)
            # response_from_model = self.generate(
            #    question=question,
            #    context="\n\n".join(
            #        [
            #            f"Ответ по куску данных номер {i}:\n\n{r}"
            #            for i, r in enumerate(relevant_chunks)
            #        ]
            #    ),
            #    system_prompt=AGGREGATE_SYSTEM_PROMPT,
            #    stream=True,
            # )
            response_from_model = "\n\n".join(relevant_chunks)
        else:
            # print("GOODE")
            # print(documents)
            # relevant_chunks = documents
            # if page_meta:
            #    context = f"document meta: {page_meta} url: {url} \n {'Это целый документ'.join(documents)}"
            # else:
            #    context = f"url: {url} \n {'Это целый документ'.join(documents)}"
            #
            response_from_model = self.generate(
                question=question,
                context="\n".join(documents),
                system_prompt=SUMARIZE_SYSTEM_PROMPT,
                stream=False,
            )
        return response_from_model

    def generate_chat_response(self, dialog_history, relevant_chunks_responses):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for conv in dialog_history:
            if conv.role == "user":
                messages.append({"role": "user", "content": conv.message})
            else:
                messages.append({"role": "assistant", "content": conv.message})
        
        messages[-1]["content"] = f"{messages[-1]['content']}\n\nКонтекст:\n```{relevant_chunks_responses}```"
        return self.client.generate(messages, stream=True)

    def generate(
        self, question, context=None, system_prompt=SYSTEM_PROMPT, stream=False
    ):
        prompt = self._make_user_query(
            question=question, context=context, system_prompt=system_prompt
        )

        template = self._build_prompt(prompt, system_prompt)
        if INFERENCE_TYPE == "llama.cpp":
            return self.client.generate(template, stream=stream)

    def get_inference_client(
        self,
        temperature,
        repeat_penalty,
        top_k,
        top_p,
        max_new_tokens,
        max_context_size,
        max_prompt_size,
    ):
        if INFERENCE_TYPE == "llama.cpp":
            return LlamaCppWrapper(
                model_path=self.model_path,
                temperature=temperature,
                repeat_penalty=repeat_penalty,
                max_tokens=max_new_tokens + max_context_size,
                n_ctx=max_context_size,
                top_k=top_k,
                top_p=top_p,
                max_prompt_size=max_prompt_size,
            )
        else:
            raise NotImplementedError

    def _make_user_query(self, question, context, system_prompt):
        if system_prompt == SYSTEM_PROMPT:
            user_query = (
                f"Контекст: {context}\n\Учитывая контекст, ответь на вопрос: {question}"
            )
        elif system_prompt == REWRITE_SYSTEM_PROMPT:
            # user_query = f"Исходный вопрос: {question}\nКонтекстная информация:\n- Метаданные: {context}\nРасширенный запрос: "
            user_query = (
                f"Перефразируй: ```{question}```\n\nИстория диалога: ```{context}```"
            )
        elif system_prompt == SUMARIZE_SYSTEM_PROMPT:
            user_query = f"Контекс: ```{context}```\n Мой вопрос: {question}"
        elif system_prompt == AGGREGATE_SYSTEM_PROMPT:
            user_query = f"Ответь на вопрос: {question}\n Контекст: {context}"
        else:
            user_query = question
        return user_query

    def _build_prompt(self, prompt, system_prompt):

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        return messages
