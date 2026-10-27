from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from src.chunker import build_chunks
from src.config import Config
from src.embeddings import EmbeddingModel
from src.evaluation import EvaluationManager
from src.pdf_loader import load_pdf
from src.retriever import Retriever
from src.reranker import SimpleReranker
from src.utils import sanitize_filename, utc_timestamp, write_json
from src.vector_store import VectorStore


class ComparatorPipeline:
    CHATBOT_FLOW_MODE = 'Mesmo fluxo do chatbot principal'

    def __init__(self):
        Config.ensure_directories()
        self.embedder = EmbeddingModel(Config.EMBEDDING_MODEL)
        self.evaluation = EvaluationManager(Config.EVALUATIONS_DIR / 'evaluations.json')
        self.reranker = SimpleReranker()

    @classmethod
    def reference_modes(cls) -> List[str]:
        return [cls.CHATBOT_FLOW_MODE]

    @staticmethod
    def _read_uploaded_bytes(uploaded_file: Any) -> bytes:
        if uploaded_file is None:
            raise ValueError('Nenhum arquivo foi enviado.')
        if hasattr(uploaded_file, 'getvalue'):
            return uploaded_file.getvalue()
        if hasattr(uploaded_file, 'read'):
            return uploaded_file.read()
        raise TypeError('Objeto de upload nao suportado.')

    @staticmethod
    def _decode_txt(raw_bytes: bytes) -> tuple[str, str]:
        for encoding in ('utf-8', 'utf-8-sig', 'latin-1'):
            try:
                return raw_bytes.decode(encoding), encoding
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError('txt', raw_bytes, 0, 1, 'Falha ao decodificar o arquivo TXT enviado.')

    @staticmethod
    def _chunk_payload(item: Dict) -> Dict:
        metadata = item.get('metadata', item)
        return {
            'chunk_id': metadata.get('chunk_id'),
            'text': metadata.get('text'),
            'title': metadata.get('title'),
            'doi': metadata.get('doi'),
            'display_reference': metadata.get('display_reference'),
            'pdf_name': metadata.get('pdf_name'),
            'page_start': metadata.get('page_start'),
            'page_end': metadata.get('page_end'),
            'vector_score': item.get('vector_score'),
            'retrieval_mode': item.get('retrieval_mode'),
        }

    @staticmethod
    def _build_sources(contexts: List[Dict]) -> List[Dict]:
        sources: List[Dict] = []
        for item in contexts:
            metadata = item['metadata']
            sources.append(
                {
                    'pdf_name': metadata.get('pdf_name'),
                    'title': metadata.get('title'),
                    'doi': metadata.get('doi'),
                    'display_reference': metadata.get('display_reference'),
                    'page_start': metadata.get('page_start'),
                    'page_end': metadata.get('page_end'),
                    'chunk_id': metadata.get('chunk_id'),
                    'vector_score': item.get('vector_score', 0.0),
                    'lexical_overlap': item.get('lexical_overlap', 0.0),
                    'weighted_score': item.get('weighted_score', 0.0),
                    'retrieval_mode': item.get('retrieval_mode', 'primary_threshold'),
                }
            )
        return sources

    @staticmethod
    def _limit_text(text: str, max_chars: int) -> tuple[str, bool]:
        if len(text) <= max_chars:
            return text, False
        return text[:max_chars].rstrip(), True

    @staticmethod
    def _join_reference_parts(parts: List[str], max_chars: int) -> tuple[str, bool]:
        reference_parts: List[str] = []
        current_chars = 0
        truncated = False

        for part in parts:
            cleaned_part = (part or '').strip()
            if not cleaned_part:
                continue

            separator = '\n\n' if reference_parts else ''
            remaining = max_chars - current_chars - len(separator)
            if remaining <= 0:
                truncated = True
                break

            if len(cleaned_part) > remaining:
                reference_parts.append(separator + cleaned_part[:remaining].rstrip())
                truncated = True
                break

            reference_parts.append(separator + cleaned_part)
            current_chars += len(separator) + len(cleaned_part)

        return ''.join(reference_parts).strip(), truncated

    @staticmethod
    def _flatten_chunks(documents: List[Dict]) -> List[Dict]:
        chunks: List[Dict] = []
        for document in documents:
            for chunk in document.get('chunks', []):
                chunks.append(chunk)
        return chunks

    @staticmethod
    def _reference_summary_item(document: Dict, used_text: str, retrieval_mode: str) -> Dict:
        scientific_metadata = document.get('scientific_metadata', {})
        return {
            'chunk_id': f"{document.get('file_stem', 'documento')}_full_text",
            'text': used_text,
            'title': scientific_metadata.get('title'),
            'doi': scientific_metadata.get('doi'),
            'display_reference': scientific_metadata.get('display_reference') or document.get('file_name'),
            'pdf_name': document.get('file_name'),
            'page_start': 1 if document.get('page_count') else None,
            'page_end': document.get('page_count'),
            'vector_score': None,
            'retrieval_mode': retrieval_mode,
        }

    def read_txt_upload(self, uploaded_file: Any) -> Dict:
        raw_bytes = self._read_uploaded_bytes(uploaded_file)
        text, encoding = self._decode_txt(raw_bytes)
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError('O arquivo TXT enviado esta vazio.')

        return {
            'file_name': getattr(uploaded_file, 'name', 'resposta.txt'),
            'encoding': encoding,
            'size_bytes': len(raw_bytes),
            'text': cleaned_text,
            'raw_bytes': raw_bytes,
        }

    def _create_session_directories(self) -> Dict[str, Path | str]:
        session_id = f"{utc_timestamp().replace(':', '').replace('-', '').replace('Z', '')}_{uuid4().hex[:8]}"
        uploads_dir = Config.COMPARATOR_UPLOADS_DIR / session_id
        processed_dir = Config.COMPARATOR_PROCESSED_DIR / session_id
        vector_store_dir = Config.COMPARATOR_VECTOR_STORE_DIR / session_id

        uploads_dir.mkdir(parents=True, exist_ok=True)
        processed_dir.mkdir(parents=True, exist_ok=True)
        vector_store_dir.mkdir(parents=True, exist_ok=True)

        return {
            'session_id': session_id,
            'uploads_dir': uploads_dir,
            'processed_dir': processed_dir,
            'vector_store_dir': vector_store_dir,
        }

    def _save_uploaded_file(self, uploaded_file: Any, target_dir: Path) -> Path:
        file_name = sanitize_filename(getattr(uploaded_file, 'name', 'arquivo_enviado'))
        target_path = target_dir / file_name
        target_path.write_bytes(self._read_uploaded_bytes(uploaded_file))
        return target_path

    def _process_uploaded_pdf(self, pdf_path: Path, processed_root: Path) -> Dict:
        pdf_data = load_pdf(pdf_path)
        scientific_metadata = pdf_data.get('scientific_metadata', {})
        chunks = build_chunks(
            pdf_data.get('pages', []),
            chunk_size=Config.CHUNK_SIZE,
            overlap=Config.CHUNK_OVERLAP,
            pdf_name=pdf_data.get('file_name', pdf_path.name),
            scientific_metadata=scientific_metadata,
        )

        processed_dir = processed_root / sanitize_filename(pdf_data.get('file_stem', pdf_path.stem))
        processed_dir.mkdir(parents=True, exist_ok=True)

        write_json(
            processed_dir / 'metadata.json',
            {
                'pdf_name': pdf_data.get('file_name'),
                'page_count': pdf_data.get('page_count', 0),
                'chunk_count': len(chunks),
                'loader': pdf_data.get('loader'),
                'scientific_metadata': scientific_metadata,
                'errors': pdf_data.get('errors', []),
            },
        )
        write_json(
            processed_dir / 'cleaned_text.json',
            {
                'full_cleaned_text': pdf_data.get('full_cleaned_text', ''),
                'pages': pdf_data.get('pages', []),
            },
        )
        write_json(processed_dir / 'chunks.json', chunks)

        return {
            **pdf_data,
            'chunks': chunks,
            'processed_dir': processed_dir,
        }

    def _build_vector_store(self, chunks: List[Dict], vector_store_dir: Path) -> VectorStore:
        if not chunks:
            raise ValueError('Nenhum chunk foi gerado a partir dos PDFs enviados.')

        texts = [chunk.get('text', '') for chunk in chunks]
        vectors = self.embedder.encode(texts, normalize=True)

        vector_store = VectorStore(self.embedder.dimension)
        vector_store.add(vectors, chunks)
        vector_store.save(vector_store_dir, embedding_model=Config.EMBEDDING_MODEL)
        vector_store.validate()
        return vector_store

    def _reference_from_chatbot_flow(
        self,
        vector_store: VectorStore,
        question: str,
        top_k: int,
    ) -> Dict:
        cleaned_question = (question or '').strip()
        if not cleaned_question:
            return {
                'status': 'error',
                'reference_text': '',
                'chunks': [],
                'logs': {'mode': 'chatbot_flow'},
                'error': 'Informe a pergunta usada na avaliacao para seguir o mesmo fluxo do chatbot principal.',
            }

        retriever = Retriever(self.embedder, vector_store)
        retrieved = retriever.retrieve(cleaned_question)
        reranked = self.reranker.rerank(cleaned_question, retrieved)
        top_contexts = reranked[:top_k]

        if not top_contexts:
            return {
                'status': 'not_run',
                'reference_text': '',
                'chunks': [],
                'logs': {
                    'mode': 'chatbot_flow',
                    'question': cleaned_question,
                    'top_k': top_k,
                    'reference_count': 0,
                    'source_metadata': [],
                },
                'note': 'Sem contexto recuperado.',
            }

        references = [item['metadata'].get('text', '') for item in top_contexts]
        chunks = [self._chunk_payload(item) for item in top_contexts]
        source_metadata = self._build_sources(top_contexts)
        reference_text = '\n\n'.join(text.strip() for text in references if text and text.strip()).strip()

        return {
            'status': 'ok',
            'reference_text': reference_text,
            'chunks': chunks,
            'logs': {
                'mode': 'chatbot_flow',
                'question': cleaned_question,
                'top_k': top_k,
                'chunk_count': len(chunks),
                'reference_text_length': len(reference_text),
                'source_metadata': source_metadata,
            },
        }

    def evaluate_txt_against_pdfs(
        self,
        uploaded_pdfs: List[Any],
        txt_file: Any,
        question_or_theme: str = '',
        reference_mode: str = CHATBOT_FLOW_MODE,
        top_k: int | None = None,
        max_reference_chars: int | None = None,
    ) -> Dict:
        pdf_files = [item for item in uploaded_pdfs if item is not None]
        if not pdf_files:
            raise ValueError('Envie pelo menos um PDF para a comparacao.')
        if txt_file is None:
            raise ValueError('Envie o arquivo TXT com a resposta a ser avaliada.')

        session = self._create_session_directories()
        txt_data = self.read_txt_upload(txt_file)
        txt_path = session['uploads_dir'] / sanitize_filename(txt_data['file_name'])
        txt_path.write_bytes(txt_data['raw_bytes'])

        documents: List[Dict] = []
        for uploaded_pdf in pdf_files:
            saved_pdf_path = self._save_uploaded_file(uploaded_pdf, session['uploads_dir'])
            documents.append(self._process_uploaded_pdf(saved_pdf_path, session['processed_dir']))

        all_chunks = self._flatten_chunks(documents)
        vector_store = self._build_vector_store(all_chunks, session['vector_store_dir'])

        top_k_value = max(int(top_k or Config.TOP_K), 1)
        reference_data = self._reference_from_chatbot_flow(
            vector_store=vector_store,
            question=question_or_theme,
            top_k=top_k_value,
        )

        if reference_data.get('status') == 'not_run':
            bertscore = {
                'status': 'not_run',
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0,
                'precision_percent': 0.0,
                'recall_percent': 0.0,
                'f1_percent': 0.0,
                'note': 'Sem contexto recuperado.',
                'reference_text': '',
                'candidate_text': txt_data['text'],
                'logs': reference_data.get('logs', {}),
            }
            return {
                'status': 'not_run',
                'session_id': session['session_id'],
                'question_or_theme': question_or_theme.strip() or None,
                'reference_mode': self.CHATBOT_FLOW_MODE,
                'top_k': top_k_value,
                'txt': {
                    'file_name': txt_data['file_name'],
                    'encoding': txt_data['encoding'],
                    'text': txt_data['text'],
                },
                'documents': [
                    {
                        'file_name': document.get('file_name'),
                        'file_stem': document.get('file_stem'),
                        'page_count': document.get('page_count'),
                        'chunk_count': len(document.get('chunks', [])),
                        'scientific_metadata': document.get('scientific_metadata', {}),
                        'errors': document.get('errors', []),
                        'processed_dir': str(document.get('processed_dir')),
                    }
                    for document in documents
                ],
                'reference': {
                    'status': 'not_run',
                    'reference_text': '',
                    'chunks': [],
                    'logs': reference_data.get('logs', {}),
                },
                'bertscore': bertscore,
                'paths': {
                    'uploads_dir': str(session['uploads_dir']),
                    'processed_dir': str(session['processed_dir']),
                    'vector_store_dir': str(session['vector_store_dir']),
                },
                'logs': {
                    'uploaded_pdf_count': len(pdf_files),
                    'generated_chunk_count': len(all_chunks),
                    'vector_store_stats': vector_store.stats(),
                    'txt_file_name': txt_data['file_name'],
                    'txt_encoding': txt_data['encoding'],
                    'reference_logs': reference_data.get('logs', {}),
                    'bertscore_logs': bertscore.get('logs', {}),
                },
                'error': None,
            }

        if reference_data.get('status') != 'ok':
            return {
                'status': 'error',
                'session_id': session['session_id'],
                'question_or_theme': question_or_theme.strip() or None,
                'reference_mode': self.CHATBOT_FLOW_MODE,
                'top_k': top_k_value,
                'txt': {
                    'file_name': txt_data['file_name'],
                    'encoding': txt_data['encoding'],
                    'text': txt_data['text'],
                },
                'documents': documents,
                'reference': reference_data,
                'paths': {
                    'uploads_dir': str(session['uploads_dir']),
                    'processed_dir': str(session['processed_dir']),
                    'vector_store_dir': str(session['vector_store_dir']),
                },
                'error': reference_data.get('error'),
            }

        bertscore = self.evaluation.calculate_bertscore(txt_data['text'], reference_data['reference_text'])
        reference_payload = {
            'status': reference_data.get('status'),
            'reference_text': reference_data.get('reference_text'),
            'chunks': reference_data.get('chunks', []),
            'logs': reference_data.get('logs', {}),
        }

        result = {
            'status': bertscore.get('status', 'error'),
            'session_id': session['session_id'],
            'question_or_theme': question_or_theme.strip() or None,
            'reference_mode': self.CHATBOT_FLOW_MODE,
            'top_k': top_k_value,
            'txt': {
                'file_name': txt_data['file_name'],
                'encoding': txt_data['encoding'],
                'text': txt_data['text'],
            },
            'documents': [
                {
                    'file_name': document.get('file_name'),
                    'file_stem': document.get('file_stem'),
                    'page_count': document.get('page_count'),
                    'chunk_count': len(document.get('chunks', [])),
                    'scientific_metadata': document.get('scientific_metadata', {}),
                    'errors': document.get('errors', []),
                    'processed_dir': str(document.get('processed_dir')),
                }
                for document in documents
            ],
            'reference': reference_payload,
            'bertscore': {
                **bertscore,
                'reference_text': reference_data.get('reference_text'),
                'candidate_text': txt_data['text'],
            },
            'paths': {
                'uploads_dir': str(session['uploads_dir']),
                'processed_dir': str(session['processed_dir']),
                'vector_store_dir': str(session['vector_store_dir']),
            },
            'logs': {
                'uploaded_pdf_count': len(pdf_files),
                'generated_chunk_count': len(all_chunks),
                'vector_store_stats': vector_store.stats(),
                'txt_file_name': txt_data['file_name'],
                'txt_encoding': txt_data['encoding'],
                'reference_logs': reference_data.get('logs', {}),
                'bertscore_logs': bertscore.get('logs', {}),
            },
        }

        write_json(
            Path(session['processed_dir']) / 'comparison_result.json',
            result,
        )
        return result
