from __future__ import annotations

import math
from typing import Dict, List

import numpy as np

from src.config import Config


class Retriever:
    def __init__(self, embedder, vector_store):
        self.embedder = embedder
        self.vector_store = vector_store

    def inspect(self, query: str, top_k: int | None = None, score_threshold: float | None = None) -> Dict:
        top_k = top_k or Config.TOP_K
        score_threshold = score_threshold if score_threshold is not None else Config.SCORE_THRESHOLD

        query_vector = self.embedder.encode([query], normalize=True)
        raw_results = self.vector_store.search(query_vector, top_k)
        filtered_results = []
        for item in raw_results:
            if item['vector_score'] >= score_threshold:
                selected = dict(item)
                selected['retrieval_mode'] = 'primary_threshold'
                filtered_results.append(selected)

        return {
            'query': query,
            'top_k': top_k,
            'score_threshold': score_threshold,
            'fallback_threshold': Config.SCORE_FALLBACK_THRESHOLD,
            'query_embedding_shape': tuple(query_vector.shape),
            'query_embedding_norm': float(np.linalg.norm(query_vector[0])) if len(query_vector) else math.nan,
            'raw_results': raw_results,
            'filtered_results': filtered_results,
        }

    def _debug_log(self, debug_info: Dict) -> None:
        self._safe_print('[RAG DEBUG] retrieval summary:')
        self._safe_print(
            {
                'query': debug_info['query'],
                'top_k': debug_info['top_k'],
                'score_threshold': debug_info['score_threshold'],
                'fallback_threshold': debug_info['fallback_threshold'],
                'query_embedding_shape': debug_info['query_embedding_shape'],
                'query_embedding_norm': round(debug_info['query_embedding_norm'], 6),
                'raw_count': len(debug_info['raw_results']),
                'filtered_count': len(debug_info['filtered_results']),
            }
        )
        for rank, item in enumerate(debug_info['raw_results'], start=1):
            metadata = item['metadata']
            preview = (metadata.get('text', '') or '')[:120].replace('\n', ' ')
            self._safe_print(
                {
                    'rank': rank,
                    'score': round(item['vector_score'], 6),
                    'chunk_id': metadata.get('chunk_id'),
                    'title': metadata.get('title'),
                    'doi': metadata.get('doi'),
                    'pdf_name': metadata.get('pdf_name'),
                    'page_start': metadata.get('page_start'),
                    'text_preview': preview,
                }
            )

    @staticmethod
    def _safe_print(payload) -> None:
        text = str(payload)
        try:
            print(text)
        except UnicodeEncodeError:
            print(text.encode('ascii', errors='backslashreplace').decode('ascii'))

    def retrieve(self, query: str, top_k: int | None = None, score_threshold: float | None = None) -> List[Dict]:
        debug_info = self.inspect(query, top_k=top_k, score_threshold=score_threshold)
        results = debug_info['filtered_results']

        if not results and debug_info['raw_results']:
            fallback = []
            for item in debug_info['raw_results']:
                if item['vector_score'] >= Config.SCORE_FALLBACK_THRESHOLD:
                    selected = dict(item)
                    selected['retrieval_mode'] = 'fallback_threshold'
                    fallback.append(selected)
            results = fallback

        if Config.RAG_DEBUG:
            self._debug_log(debug_info)
            if results:
                self._safe_print(
                    {
                        'selected_count': len(results),
                        'selected_mode': results[0].get('retrieval_mode', 'primary_threshold'),
                    }
                )
            else:
                self._safe_print('[RAG DEBUG] no results survived threshold or fallback.')

        return results
