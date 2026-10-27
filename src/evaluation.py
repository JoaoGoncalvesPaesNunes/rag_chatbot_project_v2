from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List

from src.config import Config
from src.utils import append_json_list, utc_timestamp


class EvaluationManager:
    def __init__(self, output_path: Path):
        self.output_path = output_path

    @staticmethod
    def _resolve_local_model_path(model_name: str) -> str:
        cache_root = Path.home() / '.cache' / 'huggingface' / 'hub'
        model_dir = cache_root / f"models--{model_name.replace('/', '--')}" / 'snapshots'
        if not model_dir.exists():
            return model_name

        snapshots = [path for path in model_dir.iterdir() if path.is_dir()]
        if not snapshots:
            return model_name

        return str(sorted(snapshots)[-1])

    @staticmethod
    def _to_percent(value: float | None) -> float | None:
        if value is None:
            return None
        return round(value * 100, 2)

    def calculate_bertscore(self, candidate_text: str, reference_text: str) -> Dict:
        logs = {
            'candidate_length': len(candidate_text or ''),
            'reference_text_length': len(reference_text or ''),
            'bert_score_model': Config.BERT_SCORE_MODEL,
            'bert_score_num_layers': Config.BERT_SCORE_NUM_LAYERS,
        }

        if not candidate_text or not reference_text:
            return {
                'status': 'error',
                'precision': None,
                'recall': None,
                'f1': None,
                'precision_percent': None,
                'recall_percent': None,
                'f1_percent': None,
                'error': 'BERTScore nao pode ser calculado sem resposta e texto de referencia.',
                'logs': logs,
            }

        previous_hf_offline = os.environ.get('HF_HUB_OFFLINE')
        previous_transformers_offline = os.environ.get('TRANSFORMERS_OFFLINE')
        try:
            from bert_score import score

            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            model_type = self._resolve_local_model_path(Config.BERT_SCORE_MODEL)

            precision, recall, f1 = score(
                [candidate_text],
                [reference_text],
                model_type=model_type,
                num_layers=Config.BERT_SCORE_NUM_LAYERS,
                verbose=False,
            )
            precision_value = float(precision.mean().item())
            recall_value = float(recall.mean().item())
            f1_value = float(f1.mean().item())
            return {
                'status': 'ok',
                'precision': precision_value,
                'recall': recall_value,
                'f1': f1_value,
                'precision_percent': self._to_percent(precision_value),
                'recall_percent': self._to_percent(recall_value),
                'f1_percent': self._to_percent(f1_value),
                'logs': logs,
            }
        except Exception as exc:
            logs['error'] = str(exc)
            return {
                'status': 'error',
                'precision': None,
                'recall': None,
                'f1': None,
                'precision_percent': None,
                'recall_percent': None,
                'f1_percent': None,
                'error': str(exc),
                'logs': logs,
            }
        finally:
            if previous_hf_offline is None:
                os.environ.pop('HF_HUB_OFFLINE', None)
            else:
                os.environ['HF_HUB_OFFLINE'] = previous_hf_offline

            if previous_transformers_offline is None:
                os.environ.pop('TRANSFORMERS_OFFLINE', None)
            else:
                os.environ['TRANSFORMERS_OFFLINE'] = previous_transformers_offline

    def compare_two_answers_with_bertscore(
        self,
        fisio_answer: str,
        other_answer: str,
        reference_text: str,
    ) -> Dict:
        fisio = self.calculate_bertscore(fisio_answer, reference_text)
        other = self.calculate_bertscore(other_answer, reference_text)

        if fisio['status'] != 'ok' or other['status'] != 'ok':
            return {
                'status': 'error',
                'fisio': fisio,
                'other': other,
                'winner': None,
                'logs': {
                    'reason': 'Falha no calculo do BERTScore para uma ou ambas as respostas.',
                },
                'error': fisio.get('error') or other.get('error') or 'Falha ao comparar respostas.',
            }

        difference = abs((fisio['f1'] or 0.0) - (other['f1'] or 0.0))
        if difference < 0.005:
            winner = 'Empate'
        elif (fisio['f1'] or 0.0) > (other['f1'] or 0.0):
            winner = 'Chatbot Fisio'
        else:
            winner = 'Outro Chatbot'

        return {
            'status': 'ok',
            'fisio': fisio,
            'other': other,
            'winner': winner,
            'logs': {
                'f1_difference': round(difference, 6),
            },
        }

    def bertscore(
        self,
        candidate: str,
        references: List[str],
        question: str | None = None,
        source_metadata: List[Dict] | None = None,
    ) -> Dict:
        reference_text = '\n\n'.join(text.strip() for text in references if text and text.strip()).strip()
        logs = {
            'question': question,
            'reference_count': len(references),
            'reference_text_length': len(reference_text),
            'candidate_length': len(candidate or ''),
            'bert_score_model': Config.BERT_SCORE_MODEL,
            'bert_score_num_layers': Config.BERT_SCORE_NUM_LAYERS,
            'source_metadata': source_metadata or [],
        }

        if not candidate or not reference_text:
            return {
                'status': 'not_run',
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0,
                'precision_percent': 0.0,
                'recall_percent': 0.0,
                'f1_percent': 0.0,
                'note': 'BERTScore nao calculado por falta de resposta ou contexto.',
                'reference_text': reference_text,
                'candidate_text': candidate,
                'logs': logs,
            }

        result = self.calculate_bertscore(candidate, reference_text)
        if result['status'] == 'ok':
            return {
                'status': 'ok',
                'precision': result['precision'],
                'recall': result['recall'],
                'f1': result['f1'],
                'precision_percent': result['precision_percent'],
                'recall_percent': result['recall_percent'],
                'f1_percent': result['f1_percent'],
                'note': 'BERTScore calculado com sucesso.',
                'reference_text': reference_text,
                'candidate_text': candidate,
                'logs': {**logs, **result.get('logs', {})},
            }

        return {
            'status': 'unavailable',
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'precision_percent': 0.0,
            'recall_percent': 0.0,
            'f1_percent': 0.0,
            'note': f"BERTScore indisponivel: {result.get('error', 'erro desconhecido')}",
            'reference_text': reference_text,
            'candidate_text': candidate,
            'logs': {**logs, **result.get('logs', {})},
        }

    def save_evaluation(self, payload: Dict) -> None:
        record = dict(payload)
        record.setdefault('timestamp', utc_timestamp())
        append_json_list(self.output_path, record)
