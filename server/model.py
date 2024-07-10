from llama_cpp import Llama

LLM_PATH = "models/Mistral-7B-Instruct-v0.3-Q8_0.gguf"
LLM_MODEL = "Mistral-7B-Instruct-v0.3-Q8_0.gguf"
INFERENCE_TYPE = "llama.cpp"
PROMPT_TEMPLATE_END_OF_TURN = """<|im_end|>"""
PROMPT_TEMPLATE_START_OF_TURN = """<|im_start|>"""


SYSTEM_PROMPT = """Ты Q/A бот для поиска, суммаризации, объяснения и помощи работы с статьями, если статья написана не на русском выдавай ответ на русском, не переводя технические термины, тебе будет предоставленн контекст статьи с ссылками, текстовой информацией в разрозненном виде, твоя задача помогать мне с любыми запросами что я тебя попрошу сделать с контекстом в виде статьи, которой ты получишь. Формат ответа.

Контекст: # Settings¶
Use the following options to configure Uvicorn, when running from the command line.

If you're running programmatically, using uvicorn.run(...), then use equivalent keyword arguments, eg. uvicorn.run("example:app", port=5000, reload=True, access_log=False). Please note that in this case, if you use reload=True or workers=NUM, you should put uvicorn.run into if __name__ == '__main__' clause in the main module.

You can also configure Uvicorn using environment variables with the prefix UVICORN_. For example, in case you want to run the app on port 5000, just set the environment variable UVICORN_PORT to 5000.

Ответь на этот вопрос: о чем эта статья?

Ответ на вопрос: Эта статья рассказывает о настройках Uvicorn - ASGI-сервера для Python. Основные моменты:

Описываются способы конфигурации Uvicorn при запуске из командной строки.
Объясняется, как настраивать Uvicorn программно, используя uvicorn.run() с соответствующими аргументами.
Упоминается возможность использования переменных окружения с префиксом UVICORN_ для конфигурации.
Даются советы по использованию некоторых опций, таких как reload и workers, при программном запуске.
Приводится пример использования переменной окружения для изменения порта, на котором запускается приложение.
Статья в целом посвящена различным методам настройки и конфигурации Uvicorn для разных сценариев использования.
"""
REWRITE_SYSTEM_PROMPT = "Ты бот, который помогает перефразировать пользовательские вопросы в более полные. Не отвечай на вопрос, а переписывай его. Формат ответа.\n\nВопрос: Суммаризируй\nПерефразированный: Суммаризируй страницу, по данному контексту и выдели ключевые моменты."


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

    def generate(self, question, context=None, system_prompt="answer"):
        if context:
            prompt = f"Контекст: {context}\n\nОтветь на этот вопрос: {question}\n\nОтвет на вопрос:"
        else:
            prompt = question
        template = self.build_prompt_by_template_mistral(prompt, system_prompt)
        if INFERENCE_TYPE == "llama.cpp":
            return self.llama_cpp_request(template)

    def llama_cpp_request(self, template):
        generator = self.client.model.create_completion(
            template,
            # stream=True,
            max_tokens=self.max_new_tokens,
            temperature=self.temperature,
        )
        return generator["choices"][0]["text"]
        # for token in generator:
        #    yield token["choices"][0]["text"]

    def build_prompt_by_template_mistral(self, prompt, system_prompt):
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

    def build_prompt_by_template_llama3(self, prompt, system_prompt):
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
