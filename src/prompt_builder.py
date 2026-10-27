from __future__ import annotations

from typing import Dict, List

class PromptBuilder:
    def build(self, question: str, contexts: List[Dict]) -> str:
        context_blocks: List[str] = []
        for item in contexts:
            metadata = item['metadata']
            reference = metadata.get('display_reference') or metadata.get('title') or metadata.get('pdf_name')
            pages = f"{metadata.get('page_start')}-{metadata.get('page_end')}"
            score = item.get('weighted_score', item.get('vector_score', 0.0))
            context_blocks.append(
                '\n'.join(
                    [
                        f"[Fonte: {reference}]",
                        f"[Paginas: {pages}]",
                        f"[Chunk: {metadata.get('chunk_id')}]",
                        f"[Score: {score:.4f}]",
                        metadata.get('text', ''),
                    ]
                ).strip()
            )

        context_text = '\n\n'.join(context_blocks)

        return f"""
Voce e um chatbot academico de dominio fechado, confiavel e rastreavel.

Regras obrigatorias:
1. Responda somente com base no CONTEXTO RECUPERADO.
2. Nao use conhecimento externo nem invente fontes.
3. Se nao houver evidencia suficiente, diga isso de forma explicita.
4. Justifique a resposta com base nas evidencias recuperadas.
5. Ao citar fontes, priorize titulo e DOI. So use o nome do arquivo se nao houver metadado melhor.
6. Mencione limitacoes da base quando a evidencia for parcial ou inconclusiva.
7. Nao exponha raciocinio oculto. Produza apenas justificativa verificavel.

Formato da resposta:
- Resposta
- Trechos dos PDFs usados na resposta
- Justificativa
- Limitacoes da base
- Referencias

Pergunta do usuario:
{question}

Contexto recuperado:
{context_text}
""".strip()
