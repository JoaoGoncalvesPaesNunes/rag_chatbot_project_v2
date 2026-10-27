from __future__ import annotations

from typing import Dict, List

from src.config import Config
from src.database import ResearchDatabase
from src.embeddings import EmbeddingModel
from src.evaluation import EvaluationManager
from src.history_manager import HistoryManager
from src.llm_client import DeepSeekClient
from src.prompt_builder import PromptBuilder
from src.reranker import SimpleReranker
from src.retriever import Retriever
from src.utils import utc_timestamp
from src.vector_store import VectorStore


class AcademicRAGChatbot:
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

        indexed_model = self.vector_store.manifest.get('embedding_model')
        if indexed_model and indexed_model != Config.EMBEDDING_MODEL:
            raise ValueError(
                'O indice FAISS foi gerado com um modelo de embeddings diferente do configurado. '
                f'Indice: {indexed_model} | Config atual: {Config.EMBEDDING_MODEL}. '
                'Reindexe os PDFs com python index_pdfs.py.'
            )

        self.retriever = Retriever(self.embedder, self.vector_store)
        self.reranker = SimpleReranker()
        self.prompt_builder = PromptBuilder()
        self.llm = DeepSeekClient()
        self.history = HistoryManager(Config.CONVERSATIONS_DIR / 'history.json')
        self.evaluation = EvaluationManager(Config.EVALUATIONS_DIR / 'evaluations.json')
        self.database = ResearchDatabase(Config.SQLITE_DB_PATH)

    def _build_sources(self, contexts: List[Dict]) -> List[Dict]:
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

    def _build_result(
        self,
        *,
        question: str,
        answer: str,
        contexts: List[Dict],
        bertscore: Dict,
        insufficient_evidence: bool,
        errors: List[str],
    ) -> Dict:
        retrieved_chunks = [item['metadata'] for item in contexts]
        sources = self._build_sources(contexts)
        scores = [
            {
                'chunk_id': item['metadata'].get('chunk_id'),
                'vector_score': item.get('vector_score', 0.0),
                'lexical_overlap': item.get('lexical_overlap', 0.0),
                'weighted_score': item.get('weighted_score', 0.0),
                'retrieval_mode': item.get('retrieval_mode', 'primary_threshold'),
                'title': item['metadata'].get('title'),
                'doi': item['metadata'].get('doi'),
                'display_reference': item['metadata'].get('display_reference'),
                'page_start': item['metadata'].get('page_start'),
                'page_end': item['metadata'].get('page_end'),
            }
            for item in contexts
        ]
        return {
            'timestamp': utc_timestamp(),
            'question': question,
            'answer': answer,
            'model': Config.DEEPSEEK_MODEL,
            'llm_model': Config.DEEPSEEK_MODEL,
            'retrieved_chunks': retrieved_chunks,
            'sources': sources,
            'scores': scores,
            'bertscore': bertscore,
            'insufficient_evidence': insufficient_evidence,
            'errors': errors,
        }

    def _persist(self, result: Dict) -> Dict:
        interaction_id = self.database.save_interaction(
            {
                'timestamp': result['timestamp'],
                'question': result['question'],
                'prompt_profile': None,
                'llm_model': result['llm_model'],
                'answer': result['answer'],
                'insufficient_evidence': result['insufficient_evidence'],
                'retrieved_context': result['retrieved_chunks'],
                'sources': result['sources'],
                'scores': result['scores'],
                'bertscore': result['bertscore'],
                'error': ' | '.join(result['errors']) if result['errors'] else None,
            }
        )
        evaluation_id = self.database.save_bert_evaluation(
            interaction_id,
            {
                'precision': result['bertscore'].get('precision'),
                'recall': result['bertscore'].get('recall'),
                'f1': result['bertscore'].get('f1'),
                'reference_text': result['bertscore'].get('reference_text'),
                'candidate_text': result['bertscore'].get('candidate_text'),
                'status': result['bertscore'].get('status'),
                'logs': result['bertscore'].get('logs', {}),
            },
        )
        result['interaction_id'] = interaction_id
        result['evaluation_id'] = evaluation_id
        self.history.save_interaction(result)
        self.evaluation.save_evaluation(
            {
                'question': result['question'],
                'answer': result['answer'],
                'bertscore': result['bertscore'],
                'source_chunks': [chunk.get('chunk_id') for chunk in result['retrieved_chunks']],
                'interaction_id': interaction_id,
                'evaluation_id': evaluation_id,
                'errors': result['errors'],
            }
        )
        return result

    def ask(self, question: str) -> Dict:
        retrieved = self.retriever.retrieve(question)
        reranked = self.reranker.rerank(question, retrieved)
        top_contexts = reranked[: Config.TOP_K]

        if not top_contexts:
            answer = (
                'Nao encontrei evidencia suficiente nos PDFs locais para responder com seguranca. '
                'Tente reformular a pergunta, usar termos mais proximos do conteudo indexado ou '
                'verificar se o indice foi gerado corretamente.'
            )
            bertscore = {
                'status': 'not_run',
                'precision': 0.0,
                'recall': 0.0,
                'f1': 0.0,
                'note': 'Sem contexto recuperado.',
                'reference_text': '',
                'candidate_text': answer,
                'logs': {
                    'question': question,
                    'reference_count': 0,
                    'source_metadata': [],
                },
            }
            result = self._build_result(
                question=question,
                answer=answer,
                contexts=[],
                bertscore=bertscore,
                insufficient_evidence=True,
                errors=[],
            )
            return self._persist(result)

        prompt = self.prompt_builder.build(question, top_contexts)
        errors: List[str] = []
        answer = ''
        try:
            answer = self.llm.generate(prompt)
        except Exception as exc:
            errors.append(str(exc))
            answer = (
                'O contexto foi recuperado, mas houve falha ao consultar a DeepSeek API. '
                'Verifique a chave, a conectividade e tente novamente.'
            )

        references = [item['metadata'].get('text', '') for item in top_contexts]
        bertscore = self.evaluation.bertscore(
            candidate=answer,
            references=references,
            question=question,
            source_metadata=self._build_sources(top_contexts),
        )

        result = self._build_result(
            question=question,
            answer=answer,
            contexts=top_contexts,
            bertscore=bertscore,
            insufficient_evidence=False,
            errors=errors,
        )
        return self._persist(result)
