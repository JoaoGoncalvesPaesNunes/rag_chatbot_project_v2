from __future__ import annotations

from typing import Dict, Optional

import requests

from src.config import Config


class DeepSeekClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, timeout: Optional[int] = None):
        self.api_key = api_key or Config.DEEPSEEK_API_KEY
        self.model = model or Config.DEEPSEEK_MODEL
        self.timeout = timeout or Config.DEEPSEEK_TIMEOUT
        self.base_url = 'https://api.deepseek.com/v1/chat/completions'

    def generate(self, prompt: str, temperature: float = 0.1) -> str:
        if not self.api_key:
            raise ValueError('DEEPSEEK_API_KEY não configurada.')

        payload: Dict = {
            'model': self.model,
            'temperature': temperature,
            'messages': [
                {'role': 'system', 'content': 'Você deve responder apenas com base no contexto fornecido.'},
                {'role': 'user', 'content': prompt},
            ],
        }
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                'Falha ao consultar a API da DeepSeek. '
                'Verifique a chave, a conectividade com a internet e o modelo configurado.'
            ) from exc
        data = response.json()
        return data['choices'][0]['message']['content'].strip()
