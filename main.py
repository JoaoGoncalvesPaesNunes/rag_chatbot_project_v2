from __future__ import annotations

from src.chatbot import AcademicRAGChatbot
from src.ui_helpers import format_sources


def main() -> None:
    bot = AcademicRAGChatbot()
    print('Chatbot academico RAG iniciado. Digite "sair" para encerrar.')

    while True:
        question = input('\nPergunta: ').strip()
        if question.lower() in {'sair', 'exit', 'quit'}:
            print('Encerrando.')
            break

        if not question:
            print('Digite uma pergunta para continuar.')
            continue

        result = bot.ask(question)

        print('\n=== Resposta ===')
        print(result['answer'])

        print('\n=== BERTScore ===')
        print(
            {
                'status': result['bertscore'].get('status'),
                'precision': result['bertscore'].get('precision'),
                'recall': result['bertscore'].get('recall'),
                'f1': result['bertscore'].get('f1'),
                'note': result['bertscore'].get('note'),
            }
        )

        print('\n=== Fontes ===')
        for line in format_sources(
            [
                {
                    'metadata': chunk,
                    'weighted_score': score.get('weighted_score', 0.0),
                    'vector_score': score.get('vector_score', 0.0),
                }
                for chunk, score in zip(result['retrieved_chunks'], result['scores'])
            ]
        ):
            print('-', line)

        print('\n=== Registro ===')
        print(
            {
                'interaction_id': result.get('interaction_id'),
                'evaluation_id': result.get('evaluation_id'),
                'insufficient_evidence': result.get('insufficient_evidence'),
            }
        )


if __name__ == '__main__':
    main()
