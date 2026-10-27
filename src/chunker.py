from __future__ import annotations

from typing import Dict, List


def build_chunks(
    pages: List[Dict],
    chunk_size: int = 500,
    overlap: int = 100,
    pdf_name: str = '',
    scientific_metadata: Dict | None = None,
) -> List[Dict]:
    chunks: List[Dict] = []
    chunk_id = 0
    scientific_metadata = scientific_metadata or {}
    title = scientific_metadata.get('title')
    doi = scientific_metadata.get('doi')
    display_reference = scientific_metadata.get('display_reference') or pdf_name or 'metadado nao identificado'

    for page in pages:
        if not isinstance(page, dict):
            continue

        text = page.get('cleaned_text', '') or ''
        page_number = page.get('page_number')
        if page_number is None:
            continue

        paragraphs = [paragraph.strip() for paragraph in text.splitlines() if paragraph.strip()]
        if not paragraphs:
            continue

        current_words: List[str] = []
        chunk_start_word = 0

        for paragraph in paragraphs:
            words = paragraph.split()
            if not words:
                continue

            if len(current_words) + len(words) <= chunk_size:
                current_words.extend(words)
                continue

            if current_words:
                chunks.append(
                    {
                        'chunk_id': f'{page_number:03d}_chunk_{chunk_id:04d}',
                        'text': ' '.join(current_words).strip(),
                        'pdf_name': pdf_name,
                        'title': title,
                        'doi': doi,
                        'display_reference': display_reference,
                        'chunk_index': chunk_id,
                        'pages': [page_number],
                        'page_start': page_number,
                        'page_end': page_number,
                        'position_start_word': chunk_start_word,
                        'position_end_word': chunk_start_word + len(current_words),
                        'document_position': {'page_number': page_number, 'chunk_index': chunk_id},
                    }
                )
                chunk_id += 1

            overlap_words = current_words[-overlap:] if overlap > 0 else []
            chunk_start_word += max(len(current_words) - len(overlap_words), 0)
            current_words = overlap_words + words

        if current_words:
            chunks.append(
                {
                    'chunk_id': f'{page_number:03d}_chunk_{chunk_id:04d}',
                    'text': ' '.join(current_words).strip(),
                    'pdf_name': pdf_name,
                    'title': title,
                    'doi': doi,
                    'display_reference': display_reference,
                    'chunk_index': chunk_id,
                    'pages': [page_number],
                    'page_start': page_number,
                    'page_end': page_number,
                    'position_start_word': chunk_start_word,
                    'position_end_word': chunk_start_word + len(current_words),
                    'document_position': {'page_number': page_number, 'chunk_index': chunk_id},
                }
            )
            chunk_id += 1

    return chunks
