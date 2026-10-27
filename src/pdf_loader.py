from __future__ import annotations

from pathlib import Path
from typing import List, Dict

from src.metadata_extractor import extract_scientific_metadata
from src.text_cleaner import clean_text


def _load_with_pymupdf(file_path: Path) -> List[Dict]:
    import fitz  # PyMuPDF

    pages = []
    with fitz.open(file_path) as doc:
        for i, page in enumerate(doc):
            text = page.get_text('text') or ''
            pages.append({'page_number': i + 1, 'text': text})
    return pages


def _load_with_pypdf(file_path: Path) -> List[Dict]:
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ''
        pages.append({'page_number': i + 1, 'text': text})
    return pages


def load_pdf(file_path: str | Path) -> Dict:
    file_path = Path(file_path)
    errors = []

    raw_pages = []
    try:
        raw_pages = _load_with_pymupdf(file_path)
        engine = 'pymupdf'
    except Exception as exc:
        errors.append(f'PyMuPDF falhou: {exc}')
        try:
            raw_pages = _load_with_pypdf(file_path)
            engine = 'pypdf'
        except Exception as exc2:
            errors.append(f'PyPDF falhou: {exc2}')
            raise RuntimeError(f'Não foi possível ler o PDF {file_path.name}: ' + ' | '.join(errors))

    pages = []
    for page in raw_pages:
        cleaned = clean_text(page['text'])
        pages.append({
            'page_number': page['page_number'],
            'raw_text': page['text'],
            'cleaned_text': cleaned,
        })

    metadata = extract_scientific_metadata(file_path, pages)
    full_cleaned_text = '\n\n'.join(page['cleaned_text'] for page in pages if page['cleaned_text']).strip()

    return {
        'file_name': file_path.name,
        'file_stem': file_path.stem,
        'loader': engine,
        'pages': pages,
        'page_count': len(pages),
        'scientific_metadata': metadata,
        'full_cleaned_text': full_cleaned_text,
        'errors': errors,
    }
