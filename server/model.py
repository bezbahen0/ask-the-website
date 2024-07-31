from llama_cpp import Llama

from server.page_processor import get_processor
from server.vectorizer import Vectorizer

LLM_PATH = "models/Mistral-7B-Instruct-v0.3.Q4_K_M.gguf"
LLM_MODEL = "Mistral-7B-Instruct-v0.3-Q8_0.gguf"
INFERENCE_TYPE = "llama.cpp"
PROMPT_TEMPLATE_END_OF_TURN = """<|im_end|>"""
PROMPT_TEMPLATE_START_OF_TURN = """<|im_start|>"""


SYSTEM_PROMPT = """Ты Q/A бот для поиска, суммаризации, объяснения и помощи работы с статьями, если статья написана не на русском выдавай ответ на русском, не переводя технические термины, тебе будет предоставленн контекст статьи с ссылками, текстовой информацией в разрозненном виде, твоя задача помогать мне с любыми запросами что я тебя попрошу сделать с контекстом в виде статьи, которой ты получишь. Формат ответа.

Контекст: # Settings¶
Use the following options to configure Uvicorn, when running from the command line.

If you're running programmatically, using uvicorn.run(...), then use equivalent keyword arguments, eg. uvicorn.run("example:app", port=5000, reload=True, access_log=False). Please note that in this case, if you use reload=True or workers=NUM, you should put uvicorn.run into if __name__ == '__main__' clause in the main module.

You can also configure Uvicorn using environment variables with the prefix UVICORN_. For example, in case you want to run the app on port 5000, just set the environment variable UVICORN_PORT to 5000.

Учитывая контекст, ответь на вопрос: о чем эта статья?

Ответ на вопрос: Эта статья рассказывает о настройках Uvicorn - ASGI-сервера для Python. Основные моменты:

Описываются способы конфигурации Uvicorn при запуске из командной строки.
Объясняется, как настраивать Uvicorn программно, используя uvicorn.run() с соответствующими аргументами.
Упоминается возможность использования переменных окружения с префиксом UVICORN_ для конфигурации.
Даются советы по использованию некоторых опций, таких как reload и workers, при программном запуске.
Приводится пример использования переменной окружения для изменения порта, на котором запускается приложение.
Статья в целом посвящена различным методам настройки и конфигурации Uvicorn для разных сценариев использования.
"""
#REWRITE_SYSTEM_PROMPT = """Ты - ассистент по улучшению поисковых запросов. Твоя задача - расширить и уточнить исходный вопрос пользователя, чтобы улучшить семантический поиск. Пожалуйста, выполни следующие шаги:

#1. Перефразируй исходный вопрос, сохраняя его основной смысл.
#2. Добавь 2-3 связанных ключевых слова или фразы, которые могут помочь в поиске.
#3. Если в вопросе есть специфические термины, добавь их синонимы или связанные понятия.
#4. Сформулируй расширенный запрос в виде полного предложения.
#
#Не отвечай на вопрос по существу. Твоя цель - создать расширенный поисковый запрос.
#Формат промпта:
#
#Исходный вопрос: Суммаризируй
#Контекстная информация:
#- Метаданные: {"title": "Методы .find_all() и .find*() модуля BeautifulSoup4 в Python"}
#Расширенный запрос: Объясни методы .find_all() и .find*() в BeautifulSoup4 для парсинга HTML и веб-скрапинга с примерами"""


REWRITE_SYSTEM_PROMPT = """You are an advanced query expansion system. Your task is to take a user's original query and relevant document metadata, then produce a single, comprehensive expanded query. This expanded query should:

1. Maintain the core intent of the original question
2. Incorporate key information from the provided metadata
3. Add relevant domain-specific terminology
4. Include synonyms or related concepts
5. Be formulated as a single, detailed question or statement

Remember, the goal is to create one expanded query that will improve semantic search results in a vector database like ChromaDB.

Input:
Original query: [user's question]
Document metadata: [title, keywords, or other relevant information]

Output:
Expanded query: [A single, comprehensive question or statement that incorporates all the above elements]"""
class LlamaCppWrapper:
    def __init__(
        self, model_path, n_ctx, top_k, top_p, temperature, repeat_penalty, max_tokens
    ):
        self.model = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            top_k=top_k,
            top_p=top_p,
            temperature=temperature,
            repeat_penalty=repeat_penalty,
            n_gpu_layers=-1,
        )
        self.temperature = temperature
        self.max_tokens = max_tokens


class LLMClientAdapter:
    def __init__(
        self,
        temperature,
        max_new_tokens,
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
        self.top_k = top_k
        self.top_p = top_p
        self.system_prompt = system_prompt
        self.client = self.get_inference_client(
            temperature, repeat_penalty, top_k, top_p, max_new_tokens
        )
        self.vector_processor = Vectorizer()
        self.content_processor = get_processor()

    def question_answer_with_context(self, question, context, url):

        print(f"page_url: {url}")
        self.content_processor = get_processor(page_type="html")
        documents, page_meta = self.content_processor.process_page(context, url)
        print(documents)
        print(f"Количество чанков ввобще: {len(documents)}")
        rewrited_question = self.generate(
            question=question,
            context=page_meta,
            system_prompt="rewrite",
        )
        print(f"rewrited_question: {rewrited_question}")

        relevant_documents = self.vector_processor.get_relevant_documents(
            rewrited_question, documents, page_url=url
        )
        relevant_documents = self.content_processor.process_relevant_documents(relevant_documents)
        print(relevant_documents)
        relevant_chunks = [doc.page_content for doc in relevant_documents]

        response_from_model = self.generate(
            question=question, context="\n\n".join(relevant_chunks)
        )
        
        return response_from_model

    def generate(self, question, context=None, system_prompt="answer"):
        prompt = self._make_user_query(
            question=question, context=context, system_prompt=system_prompt
        )

        template = self._build_prompt_by_template_mistral(prompt, system_prompt)
        if INFERENCE_TYPE == "llama.cpp":
            if system_prompt == "rewrite":
                return self._llama_cpp_request(template, stream=False)
            elif system_prompt == "answer":
                return self._llama_cpp_request(template, stream=True)
            raise ValueError(f"{system_prompt} system_prompt not implemented")

    def get_inference_client(
        self, temperature, repeat_penalty, top_k, top_p, max_new_tokens
    ):
        if INFERENCE_TYPE == "llama.cpp":
            return LlamaCppWrapper(
                model_path=self.model_path,
                temperature=temperature,
                repeat_penalty=repeat_penalty,
                max_tokens=max_new_tokens,
                n_ctx=max_new_tokens,
                top_k=top_k,
                top_p=top_p,
            )
        else:
            raise NotImplementedError

    def _make_user_query(self, question, context, system_prompt):
        if system_prompt == "answer":
            user_query = f"Контекст: {context}\n\Учитывая контекст, ответь на вопрос: {question}\n\nОтвет на вопрос:"
        elif system_prompt == "rewrite":
            #user_query = f"Исходный вопрос: {question}\nКонтекстная информация:\n- Метаданные: {context}\nРасширенный запрос: "
            user_query = f"Input:\nOriginal query: {question}\nDocument metadata: {context}\n\nOutput:\nExpanded query: " 
        else:
            user_query = question
        return user_query

    def _make_answer_context(sefl, questin, context):
        pass

    def _llama_cpp_request(self, template, stream=False):
        response_generator = self.client.model.create_completion(
            template,
            stream=stream,
            max_tokens=self.max_new_tokens,
            temperature=self.temperature,
        )
        if stream:

            def generate():
                for token in response_generator:
                    yield token["choices"][0]["text"]

            return generate()
        return response_generator["choices"][0]["text"]

    def _build_prompt_by_template_mistral(self, prompt, system_prompt):
        system_prompt = (
            SYSTEM_PROMPT if system_prompt == "answer" else REWRITE_SYSTEM_PROMPT
        )
        template = (
            "<s>[INST] <<SYS>>\n"
            + system_prompt
            + "\n<</SYS>>\n\n"
            + prompt
            + " [/INST]"
        )
        return template

    def _build_prompt_by_template_llama3(self, prompt, system_prompt):
        template = (
            PROMPT_TEMPLATE_START_OF_TURN + "system" + self.system_prompt
            if system_prompt == "answer"
            else REWRITE_SYSTEM_PROMPT
            + PROMPT_TEMPLATE_END_OF_TURN
            + PROMPT_TEMPLATE_START_OF_TURN
            + "user"
            + prompt
            + PROMPT_TEMPLATE_END_OF_TURN
            + PROMPT_TEMPLATE_START_OF_TURN
            + "assistant"
        )
        return template
