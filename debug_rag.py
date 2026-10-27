from __future__ import annotations

import argparse
import json

from src.config import Config
from src.embeddings import EmbeddingModel
from src.retriever import Retriever
from src.vector_store import VectorStore


def _print_header(title: str) -> None:
    print(f'\n=== {title} ===')


def _safe_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=True, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description='Debug do pipeline RAG/FAISS.')
    parser.add_argument('--query', default='laser', help='Consulta para testar o retrieval.')
    parser.add_argument('--top-k', type=int, default=6, help='Quantidade de resultados a consultar.')
    args = parser.parse_args()

    _print_header('PDFs em data/raw_pdfs')
    pdf_files = sorted(Config.RAW_PDFS_DIR.glob('*.pdf'))
    print([pdf.name for pdf in pdf_files] or 'Nenhum PDF encontrado.')

    _print_header('Arquivos em data/vector_store')
    vector_files = sorted(path.name for path in Config.VECTOR_STORE_DIR.glob('*'))
    print(vector_files or 'Nenhum arquivo encontrado.')

    _print_header('Config')
    print(
        _safe_json(
            {
                'vector_store_dir': str(Config.VECTOR_STORE_DIR),
                'embedding_model': Config.EMBEDDING_MODEL,
                'score_threshold': Config.SCORE_THRESHOLD,
                'score_fallback_threshold': Config.SCORE_FALLBACK_THRESHOLD,
                'top_k': args.top_k,
            }
        )
    )

    embedder = EmbeddingModel(Config.EMBEDDING_MODEL)
    store = VectorStore(embedder.dimension)
    if not store.exists(Config.VECTOR_STORE_DIR):
        print('Falha: indice vetorial nao encontrado. Rode python index_pdfs.py primeiro.')
        return

    store.load(Config.VECTOR_STORE_DIR)
    store.validate()

    _print_header('Estatisticas do indice')
    print(_safe_json(store.stats()))
    print(f'Vetores FAISS: {store.index.ntotal}')
    print(f'Metadados: {len(store.metadata)}')

    _print_header('Primeiros 3 metadados')
    for item in store.metadata[:3]:
        preview = {
            **{key: value for key, value in item.items() if key != 'text'},
            'text_preview': (item.get('text') or '')[:180],
        }
        print(_safe_json(preview))

    retriever = Retriever(embedder, store)
    debug_info = retriever.inspect(args.query, top_k=args.top_k, score_threshold=Config.SCORE_THRESHOLD)

    _print_header(f'Debug da consulta: {args.query}')
    print(
        _safe_json(
            {
                'query_embedding_shape': debug_info['query_embedding_shape'],
                'query_embedding_norm': debug_info['query_embedding_norm'],
                'raw_hits': len(debug_info['raw_results']),
                'hits_after_primary_threshold': len(debug_info['filtered_results']),
                'primary_threshold': debug_info['score_threshold'],
                'fallback_threshold': debug_info['fallback_threshold'],
            }
        )
    )

    _print_header('Resultados brutos')
    for rank, item in enumerate(debug_info['raw_results'], start=1):
        metadata = item['metadata']
        result = {
            'rank': rank,
            'score': item['vector_score'],
            'chunk_id': metadata.get('chunk_id'),
            'title': metadata.get('title'),
            'doi': metadata.get('doi'),
            'pdf_name': metadata.get('pdf_name'),
            'page_start': metadata.get('page_start'),
            'page_end': metadata.get('page_end'),
            'text_preview': (metadata.get('text') or '')[:240],
        }
        print(_safe_json(result))

    _print_header('Resultados selecionados pelo retriever')
    selected = retriever.retrieve(args.query, top_k=args.top_k, score_threshold=Config.SCORE_THRESHOLD)
    print(
        _safe_json(
            {
                'selected_count': len(selected),
                'selected_mode': selected[0].get('retrieval_mode', 'primary_threshold') if selected else 'none',
            }
        )
    )
    for item in selected:
        metadata = item['metadata']
        print(
            _safe_json(
                {
                    'score': item['vector_score'],
                    'weighted_score': item.get('weighted_score'),
                    'chunk_id': metadata.get('chunk_id'),
                    'display_reference': metadata.get('display_reference'),
                    'page_start': metadata.get('page_start'),
                    'text_preview': (metadata.get('text') or '')[:240],
                }
            )
        )

    if store.index.ntotal == 0:
        print('Falha detectada: indice FAISS vazio.')
    elif len(store.metadata) == 0:
        print('Falha detectada: nenhum metadado persistido.')
    elif not selected:
        print('Falha detectada: nenhum chunk sobreviveu aos thresholds atuais.')
    else:
        print('Pipeline RAG aparentemente consistente para a consulta de teste.')


if __name__ == '__main__':
    main()
