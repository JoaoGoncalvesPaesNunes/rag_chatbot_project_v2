from __future__ import annotations

from typing import Dict, List

from src.config import Config
from src.embeddings import EmbeddingModel
from src.retriever import Retriever
from src.vector_store import VectorStore


class ReferenceBuilder:
    def __init__(self):
        Config.ensure_directories()
        self.embedder = EmbeddingModel(Config.EMBEDDING_MODEL)
        self.vector_store = VectorStore(self.embedder.dimension)
        if not self.vector_store.exists(Config.VECTOR_STORE_DIR):
            raise FileNotFoundError(
                f'Indice vetorial nao encontrado em {Config.VECTOR_STORE_DIR}. Rode primeiro: python index_pdfs.py'
            )

        self.vector_store.load(Config.VECTOR_STORE_DIR)
        self.vector_store.validate()
        self.retriever = Retriever(self.embedder, self.vector_store)

    @staticmethod
    def _chunk_payload(item: Dict) -> Dict:
        metadata = item['metadata']
        return {
            'chunk_id': metadata.get('chunk_id'),
            'text': metadata.get('text'),
            'title': metadata.get('title'),
            'doi': metadata.get('doi'),
            'display_reference': metadata.get('display_reference'),
            'pdf_name': metadata.get('pdf_name'),
            'page_start': metadata.get('page_start'),
            'page_end': metadata.get('page_end'),
            'vector_score': item.get('vector_score', 0.0),
            'retrieval_mode': item.get('retrieval_mode', 'primary_threshold'),
        }

    def build_reference_from_question(self, question: str, top_k: int) -> Dict:
        if not question.strip():
            return {
                'status': 'error',
                'reference_text': '',
                'chunks': [],
                'logs': {},
                'error': 'Informe uma pergunta-base para recuperar trechos relevantes.',
            }

        retrieved = self.retriever.retrieve(question, top_k=top_k)
        if not retrieved:
            return {
                'status': 'error',
                'reference_text': '',
                'chunks': [],
                'logs': {
                    'question': question,
                    'top_k': top_k,
                },
                'error': (
                    'Nao foi possivel recuperar trechos dos PDFs para usar como referencia. '
                    'Verifique se os PDFs foram indexados ou tente uma pergunta-base mais especifica.'
                ),
            }

        chunks = [self._chunk_payload(item) for item in retrieved[:top_k]]
        reference_text = '\n\n'.join(chunk['text'] for chunk in chunks if chunk.get('text')).strip()
        return {
            'status': 'ok',
            'reference_text': reference_text,
            'chunks': chunks,
            'logs': {
                'question': question,
                'top_k': top_k,
                'chunk_count': len(chunks),
            },
        }

    def build_reference_from_all_chunks(self) -> Dict:
        if not self.vector_store.metadata:
            return {
                'status': 'error',
                'reference_text': '',
                'chunks': [],
                'logs': {},
                'error': 'Nao ha chunks indexados disponiveis para usar como referencia.',
            }

        chunks: List[Dict] = []
        for metadata in self.vector_store.metadata:
            chunks.append(
                {
                    'chunk_id': metadata.get('chunk_id'),
                    'text': metadata.get('text'),
                    'title': metadata.get('title'),
                    'doi': metadata.get('doi'),
                    'display_reference': metadata.get('display_reference'),
                    'pdf_name': metadata.get('pdf_name'),
                    'page_start': metadata.get('page_start'),
                    'page_end': metadata.get('page_end'),
                    'vector_score': None,
                    'retrieval_mode': 'all_chunks',
                }
            )

        reference_text = '\n\n'.join(chunk['text'] for chunk in chunks if chunk.get('text')).strip()
        return {
            'status': 'ok',
            'reference_text': reference_text,
            'chunks': chunks,
            'logs': {
                'chunk_count': len(chunks),
                'mode': 'all_chunks',
            },
        }
