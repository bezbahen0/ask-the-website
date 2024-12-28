from llama_cpp import Llama

from server.partition import get_processor
from tqdm import tqdm


from abc import ABC, abstractmethod
from typing import Generator, Any, Optional, Callable


class StreamProcessor(ABC):
    @abstractmethod
    def process_stream(self, stream: Generator) -> Generator:
        pass


class JsonFieldStreamProcessor(StreamProcessor):
    def __init__(self, field_name: str):
        self.field_name = field_name
        self.buffer = ""
        self.in_field = False
        self.json_started = False

    def process_stream(self, stream: Generator) -> Generator:
        for token in stream:
            content = token["choices"][0]["delta"].get("content", "")
            if not content:
                continue

            self.buffer += content

            if not self.json_started and "{" in self.buffer:
                self.json_started = True

            if not self.json_started:
                continue

            field_marker = f'"{self.field_name}": "'
            if field_marker in self.buffer and not self.in_field:
                self.in_field = True
                self.buffer = self.buffer.split(field_marker)[1]

            if self.in_field:
                index = 0
                while index < len(self.buffer):
                    if self.buffer[index] == '"':
                        if index > 0 and self.buffer[index - 1] == '\\':
                            index += 1
                            continue
                        
                        field_content = self.buffer[:index]
                        self.buffer = self.buffer[index + 1:]
                        
                        if field_content:
                            yield field_content
                        
                        self.in_field = False
                        break
                    index += 1
                
                if self.in_field and self.buffer:
                    yield self.buffer
                    self.buffer = ""


class DefaultStreamProcessor(StreamProcessor):
    def process_stream(self, stream: Generator) -> Generator:
        for token in stream:
            yield token["choices"][0]["delta"].get("content", "")


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
            n_ctx=max_tokens,
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

    def generate(
        self,
        template,
        stream=False,
        schema=None,
        stream_processor=None,
    ):
        if schema:
            response_generator = self.model.create_chat_completion(
                template,
                stream=stream,
                max_tokens=self.max_new_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object", "schema": schema},
            )
        else:
            response_generator = self.model.create_chat_completion(
                template,
                stream=stream,
                max_tokens=self.max_new_tokens,
                temperature=self.temperature,
            )

        if stream:

            def generate():
                processor = (
                    stream_processor if stream_processor else DefaultStreamProcessor()
                )
                return processor.process_stream(response_generator)

            return generate()
        return response_generator["choices"][0]["message"]["content"]

    def check_context_len(self, text, return_len=False):
        context_len = len(self.tokenize(text))
        if return_len:
            return context_len

        if context_len > self.n_ctx:
            return False
        return True
