from __future__ import annotations

import os
from pathlib import Path
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    def __init__(self, model_name: str):
        self.model_name = model_name
        errors: list[str] = []
        local_model_path = self._find_local_snapshot(model_name)

        previous_hf_offline = os.environ.get('HF_HUB_OFFLINE')
        previous_transformers_offline = os.environ.get('TRANSFORMERS_OFFLINE')
        try:
            os.environ['HF_HUB_OFFLINE'] = '1'
            os.environ['TRANSFORMERS_OFFLINE'] = '1'
            self.model = SentenceTransformer(
                str(local_model_path) if local_model_path else model_name,
                local_files_only=True,
                model_kwargs={'local_files_only': True},
                tokenizer_kwargs={'local_files_only': True},
                config_kwargs={'local_files_only': True},
            )
            self.loaded_from = 'local_cache'
            return
        except Exception as exc:
            errors.append(f'local_cache: {exc}')
        finally:
            if previous_hf_offline is None:
                os.environ.pop('HF_HUB_OFFLINE', None)
            else:
                os.environ['HF_HUB_OFFLINE'] = previous_hf_offline

            if previous_transformers_offline is None:
                os.environ.pop('TRANSFORMERS_OFFLINE', None)
            else:
                os.environ['TRANSFORMERS_OFFLINE'] = previous_transformers_offline

        try:
            self.model = SentenceTransformer(model_name)
            self.loaded_from = 'remote_or_cache'
            return
        except Exception as exc:
            errors.append(f'remote_or_cache: {exc}')

        raise RuntimeError(
            'Falha ao carregar o modelo de embeddings. O projeto tentou usar o cache local e depois a carga padrao. '
            'Se esta for a primeira execucao neste ambiente, sera necessario baixar o modelo uma vez com acesso a internet. '
            f'Detalhes: {" | ".join(errors)}'
        )

    def encode(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )
        return vectors.astype('float32')

    @property
    def dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()

    @staticmethod
    def _find_local_snapshot(model_name: str) -> Path | None:
        cache_root = Path.home() / '.cache' / 'huggingface' / 'hub'
        model_dir = cache_root / f"models--{model_name.replace('/', '--')}" / 'snapshots'
        if not model_dir.exists():
            return None

        snapshots = [path for path in model_dir.iterdir() if path.is_dir()]
        if not snapshots:
            return None

        return sorted(snapshots)[-1]
