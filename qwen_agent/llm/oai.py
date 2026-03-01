import os
from pprint import pformat
from typing import Dict, Iterator, List, Optional

import openai

from qwen_agent.llm.base import ModelServiceError, register_llm
from qwen_agent.llm.function_calling import BaseFnCallModel
from qwen_agent.llm.schema import ASSISTANT, Message
from qwen_agent.log import logger


@register_llm('oai')
class TextChatAtOAI(BaseFnCallModel):

    def __init__(self, cfg: Optional[Dict] = None):
        super().__init__(cfg)
        cfg = cfg or {}

        api_base = cfg.get('api_base')
        api_base = api_base or cfg.get('base_url')
        api_base = api_base or cfg.get('model_server')
        api_base = (api_base or '').strip()

        api_key = cfg.get('api_key') or os.getenv('OPENAI_API_KEY') or 'EMPTY'
        api_key = api_key.strip()

        self.model = self.model or cfg.get('model_name', '')
        if not self.model:
            raise ValueError('Missing model name in LLM config.')

        self._client = openai.OpenAI(api_key=api_key, base_url=api_base if api_base else None)

    @staticmethod
    def convert_messages_to_dicts(messages: List[Message]) -> List[dict]:
        return [msg.model_dump() for msg in messages]

    def _chat_stream(
        self,
        messages: List[Message],
        delta_stream: bool,
        generate_cfg: dict,
    ) -> Iterator[List[Message]]:
        payload = self.convert_messages_to_dicts(messages)
        logger.debug(f'LLM Input:\n{pformat(payload, indent=2)}')

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=payload,
                stream=True,
                **generate_cfg,
            )
        except Exception as e:
            raise ModelServiceError(exception=e)

        if delta_stream:
            for chunk in response:
                delta = chunk.choices[0].delta
                content = getattr(delta, 'content', None) or ''
                reasoning_content = getattr(delta, 'reasoning_content', None) or ''
                yield [
                    Message(role=ASSISTANT,
                            content=content,
                            reasoning_content=reasoning_content,
                            extra={'model_service_info': chunk})
                ]
        else:
            full_content = ''
            full_reasoning_content = ''
            for chunk in response:
                delta = chunk.choices[0].delta
                content = getattr(delta, 'content', None)
                reasoning_content = getattr(delta, 'reasoning_content', None)
                if content:
                    full_content += content
                if reasoning_content:
                    full_reasoning_content += reasoning_content
                yield [
                    Message(role=ASSISTANT,
                            content=full_content,
                            reasoning_content=full_reasoning_content,
                            extra={'model_service_info': chunk})
                ]

    def _chat_no_stream(
        self,
        messages: List[Message],
        generate_cfg: dict,
    ) -> List[Message]:
        payload = self.convert_messages_to_dicts(messages)
        logger.debug(f'LLM Input:\n{pformat(payload, indent=2)}')
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=payload,
                stream=False,
                **generate_cfg,
            )
        except Exception as e:
            raise ModelServiceError(exception=e)

        msg = response.choices[0].message
        content = getattr(msg, 'content', None) or ''
        reasoning_content = getattr(msg, 'reasoning_content', None) or ''
        return [
            Message(role=ASSISTANT,
                    content=content,
                    reasoning_content=reasoning_content,
                    extra={'model_service_info': response})
        ]
