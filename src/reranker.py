from __future__ import annotations

from typing import Dict, List


def _lexical_overlap(query: str, text: str) -> float:
    query_terms = {t.lower() for t in query.split() if len(t) > 2}
    text_terms = {t.lower() for t in text.split() if len(t) > 2}
    if not query_terms:
        return 0.0
    return len(query_terms & text_terms) / len(query_terms)


class SimpleReranker:
    def rerank(self, query: str, results: List[Dict]) -> List[Dict]:
        reranked = []
        for item in results:
            overlap = _lexical_overlap(query, item['metadata']['text'])
            weighted = (0.8 * item['vector_score']) + (0.2 * overlap)
            updated = dict(item)
            updated['lexical_overlap'] = overlap
            updated['weighted_score'] = weighted
            reranked.append(updated)
        return sorted(reranked, key=lambda x: x['weighted_score'], reverse=True)
