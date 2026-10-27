from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Iterable, List


DOI_PATTERN = re.compile(r'\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b', re.IGNORECASE)

NOISY_TITLE_PATTERNS = (
    re.compile(r'^\s*(abstract|keywords?|introduction|references?|discussion)\s*$', re.IGNORECASE),
    re.compile(r'^\s*doi\s*[:.]', re.IGNORECASE),
    re.compile(r'^\s*page\s+\d+\s*$', re.IGNORECASE),
)


def _normalize_line(text: str) -> str:
    cleaned = ' '.join((text or '').replace('\x00', ' ').split())
    return cleaned.strip(' -|')


def _looks_like_title(line: str) -> bool:
    if not line:
        return False
    if len(line) < 12 or len(line) > 220:
        return False
    if sum(ch.isalpha() for ch in line) < 8:
        return False
    if any(pattern.match(line) for pattern in NOISY_TITLE_PATTERNS):
        return False
    lowered = line.lower()
    if lowered.startswith('http://') or lowered.startswith('https://'):
        return False
    return True


def _iter_candidate_lines(pages: Iterable[Dict], max_pages: int = 2) -> List[str]:
    lines: List[str] = []
    for page in list(pages)[:max_pages]:
        raw_text = page.get('raw_text', '') or page.get('cleaned_text', '')
        for line in raw_text.splitlines():
            normalized = _normalize_line(line)
            if normalized:
                lines.append(normalized)
    return lines


def _extract_doi(lines: Iterable[str]) -> str | None:
    for line in lines:
        match = DOI_PATTERN.search(line)
        if match:
            return match.group(0).rstrip('.,;)')
    return None


def _extract_title(lines: Iterable[str]) -> str | None:
    selected: List[str] = []
    for line in lines:
        if not _looks_like_title(line):
            continue
        selected.append(line)
        if len(selected) == 2:
            break

    if not selected:
        return None

    if len(selected) == 1:
        return selected[0]

    combined = ' '.join(selected)
    if len(combined) <= 220:
        return combined
    return selected[0]


def _fallback_title(file_path: Path, lines: Iterable[str]) -> str:
    for line in lines:
        if len(line) >= 8:
            return line

    stem = file_path.stem.replace('_', ' ').replace('-', ' ').strip()
    return stem or 'metadado nao identificado'


def build_display_reference(title: str | None, doi: str | None, pdf_name: str) -> str:
    if title and doi:
        return f'{title}. DOI: {doi}'
    if title:
        return title
    if doi:
        return f'DOI: {doi}'

    fallback_name = Path(pdf_name).stem.replace('_', ' ').replace('-', ' ').strip()
    return fallback_name or 'metadado nao identificado'


def extract_scientific_metadata(file_path: str | Path, pages: List[Dict]) -> Dict:
    file_path = Path(file_path)
    candidate_lines = _iter_candidate_lines(pages)
    doi = _extract_doi(candidate_lines)
    title = _extract_title(candidate_lines)
    fallback_title = _fallback_title(file_path, candidate_lines)

    final_title = title or fallback_title
    display_reference = build_display_reference(final_title, doi, file_path.name)

    return {
        'pdf_name': file_path.name,
        'file_stem': file_path.stem,
        'title': final_title,
        'doi': doi,
        'display_reference': display_reference,
        'page_count': len(pages),
        'first_lines': candidate_lines[:10],
        'fallback_title': fallback_title,
        'metadata_status': 'identified' if title or doi else 'fallback',
    }
