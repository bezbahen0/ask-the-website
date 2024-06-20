from llama_cpp import Llama

LLM_PATH = "./orca-2-13b.Q8_0.gguf"
INFERENCE_TYPE = "llama.cpp"
PROMPT_TEMPLATE_END_OF_TURN = """<|im_end|>"""
PROMPT_TEMPLATE_START_OF_TURN = """<|im_start|>"""


SYSTEM_PROMPT = "your task when receiving text is to summarize its contents and produce quality results"


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
        system_prompt=SYSTEM_PROMPT,
    ):
        self.model_path = model_path
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

    def generate(self, question, context=None):
        # if context:
        #    prompt = f"Контекст:\n###\n {context}\n###\nВопрос: {question}"
        # else:
        #    prompt = question
        prompt = question
        template = self.build_prompt_by_template(prompt)
        if INFERENCE_TYPE == "llama.cpp":
            yield from self.llama_cpp_request(template)

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

    def build_prompt_by_template(self, prompt):
        template = (
            PROMPT_TEMPLATE_START_OF_TURN
            + "system"
            + self.system_prompt
            + PROMPT_TEMPLATE_END_OF_TURN
            + PROMPT_TEMPLATE_START_OF_TURN
            + "user"
            + prompt
            + PROMPT_TEMPLATE_END_OF_TURN
            + PROMPT_TEMPLATE_START_OF_TURN
            + "assistant"
        )
        return template
