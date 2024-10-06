from llama_cpp import Llama

from server.partition import get_processor
from tqdm import tqdm


class LlamaCppWrapper:
    def __init__(
        self,
        model_path,
        n_ctx,
        top_k,
        top_p,
        temperature,
        repeat_penalty,
        max_tokens,
        max_prompt_size,
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
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.top_k = top_k
        self.top_p = top_p
        self.temperature = temperature
        self.repeat_penalty = repeat_penalty
        self.max_tokens = max_tokens
        self.max_new_tokens = self.max_tokens - self.n_ctx
        self.max_prompt_size = max_prompt_size

    def get_params(self):
        return {
            "n_ctx": self.n_ctx,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "temperature": self.temperature,
            "repeat_penalty": self.repeat_penalty,
            "max_tokens": self.max_tokens,
            "max_new_tokens": self.max_tokens - self.n_ctx,
            "max_prompt_size": self.max_prompt_size,
        }

    def tokenize(self, text):
        return self.model.tokenize(text.encode("utf8"))

    def generate(self, template, stream=False):
        response_generator = self.model.create_chat_completion(
            template,
            stream=stream,
            max_tokens=self.max_new_tokens,
            temperature=self.temperature,
        )
        if stream:

            def generate():
                for token in response_generator:
                    yield token["choices"][0]["delta"].get("content", "")

            return generate()
        return response_generator["choices"][0]["message"]["content"]

    def check_context_len(self, text, return_len=False):
        context_len = len(self.tokenize(text))
        if return_len:
            return context_len

        if context_len > self.n_ctx - self.max_prompt_size:
            return False
        return True
