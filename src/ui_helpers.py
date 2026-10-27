from __future__ import annotations

from typing import Dict, List


def format_sources(results: List[Dict]) -> List[str]:
    lines: List[str] = []
    for item in results:
        metadata = item['metadata']
        reference = metadata.get('display_reference') or metadata.get('title') or metadata.get('pdf_name')
        doi = metadata.get('doi') or 'DOI nao identificado'
        score = item.get('weighted_score', item.get('vector_score', 0.0))
        lines.append(
            f'{reference} | {doi} | pags. {metadata.get("page_start")}-{metadata.get("page_end")} | '
            f'{metadata.get("chunk_id")} | score={score:.3f}'
        )
    return lines
