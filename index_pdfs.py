from __future__ import annotations

from src.chunker import build_chunks
from src.config import Config
from src.embeddings import EmbeddingModel
from src.pdf_loader import load_pdf
from src.utils import sanitize_filename, write_json
from src.vector_store import VectorStore


def index_pdfs() -> None:
    Config.ensure_directories()
    embedder = EmbeddingModel(Config.EMBEDDING_MODEL)
    store = VectorStore(embedder.dimension)

    pdf_files = sorted(Config.RAW_PDFS_DIR.glob('*.pdf'))
    if not pdf_files:
        print(f'Nenhum PDF encontrado em: {Config.RAW_PDFS_DIR}')
        return

    total_chunks = 0
    for pdf_path in pdf_files:
        print(f'Processando {pdf_path.name}...')
        document = load_pdf(pdf_path)
        scientific_metadata = document['scientific_metadata']

        chunks = build_chunks(
            document['pages'],
            chunk_size=Config.CHUNK_SIZE,
            overlap=Config.CHUNK_OVERLAP,
            pdf_name=document['file_name'],
            scientific_metadata=scientific_metadata,
        )
        valid_chunks = [chunk for chunk in chunks if chunk.get('text', '').strip()]

        safe_name = sanitize_filename(pdf_path.stem)
        output_dir = Config.PROCESSED_DIR / safe_name
        output_dir.mkdir(parents=True, exist_ok=True)

        cleaned_payload = {
            'pdf_name': document['file_name'],
            'loader': document['loader'],
            'page_count': document['page_count'],
            'scientific_metadata': scientific_metadata,
            'pages': [
                {
                    'page_number': page['page_number'],
                    'cleaned_text': page['cleaned_text'],
                }
                for page in document['pages']
            ],
        }
        metadata_payload = {
            'pdf_name': document['file_name'],
            'page_count': document['page_count'],
            'loader': document['loader'],
            'chunk_count': len(valid_chunks),
            'scientific_metadata': scientific_metadata,
            'processing_errors': document.get('errors', []),
        }

        write_json(output_dir / 'cleaned_text.json', cleaned_payload)
        write_json(output_dir / 'chunks.json', valid_chunks)
        write_json(output_dir / 'metadata.json', metadata_payload)

        if not valid_chunks:
            print(f'  Aviso: nenhum chunk valido foi gerado para {pdf_path.name}.')
            continue

        vectors = embedder.encode([chunk['text'] for chunk in valid_chunks], normalize=True)
        store.add(vectors, valid_chunks)
        total_chunks += len(valid_chunks)
        print(
            f'  Chunks: {len(valid_chunks)} | '
            f'Titulo: {scientific_metadata.get("title")} | '
            f'DOI: {scientific_metadata.get("doi") or "nao identificado"}'
        )

    if store.index.ntotal == 0:
        print('Nenhum vetor foi gerado. Verifique a extracao textual dos PDFs.')
        return

    store.save(Config.VECTOR_STORE_DIR, embedding_model=Config.EMBEDDING_MODEL)
    print(
        f'Indexacao finalizada. PDFs processados: {len(pdf_files)} | '
        f'Chunks indexados: {total_chunks} | Indice salvo em: {Config.VECTOR_STORE_DIR}'
    )


if __name__ == '__main__':
    index_pdfs()
