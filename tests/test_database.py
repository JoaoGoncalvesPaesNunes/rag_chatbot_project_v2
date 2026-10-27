from pathlib import Path

from src.database import ResearchDatabase


def test_database_creates_tables_and_persists_records(tmp_path: Path):
    database = ResearchDatabase(tmp_path / 'research_data.sqlite')

    interaction_id = database.save_interaction(
        {
            'question': 'O que o artigo diz sobre laser?',
            'prompt_profile': 'academico_formal',
            'llm_model': 'deepseek-chat',
            'answer': 'Resposta de teste',
            'insufficient_evidence': False,
            'retrieved_context': [{'chunk_id': '001_chunk_0001'}],
            'sources': [{'display_reference': 'Artigo teste'}],
            'scores': [{'weighted_score': 0.9}],
            'bertscore': {'f1': 0.8},
        }
    )
    evaluation_id = database.save_bert_evaluation(
        interaction_id,
        {
            'precision': 0.8,
            'recall': 0.7,
            'f1': 0.75,
            'reference_text': 'texto de referencia',
            'candidate_text': 'texto candidato',
            'status': 'ok',
            'logs': {'note': 'teste'},
        },
    )

    interactions = database.list_interactions(limit=5)

    assert interaction_id > 0
    assert evaluation_id > 0
    assert interactions
    assert interactions[0]['id'] == interaction_id


def test_database_saves_response_comparison(tmp_path: Path):
    database = ResearchDatabase(tmp_path / 'research_data.sqlite')

    comparison_id = database.save_response_comparison(
        {
            'base_question': 'O que os artigos dizem sobre laser?',
            'top_k': 5,
            'reference_mode': 'Recuperar Top-K por pergunta',
            'reference_text': 'texto de referencia',
            'reference_chunks': [{'chunk_id': '001_chunk_0001'}],
            'chatbot_fisio_answer': 'resposta fisio',
            'other_chatbot_answer': 'outra resposta',
            'fisio': {'precision': 0.8, 'recall': 0.7, 'f1': 0.75, 'precision_percent': 80.0, 'recall_percent': 70.0, 'f1_percent': 75.0},
            'other': {'precision': 0.7, 'recall': 0.6, 'f1': 0.65, 'precision_percent': 70.0, 'recall_percent': 60.0, 'f1_percent': 65.0},
            'winner': 'Chatbot Fisio',
            'logs': {'note': 'teste'},
        }
    )

    comparisons = database.list_response_comparisons(limit=5)

    assert comparison_id > 0
    assert comparisons
    assert comparisons[0]['id'] == comparison_id


def test_database_saves_pdf_txt_bertscore_evaluation(tmp_path: Path):
    database = ResearchDatabase(tmp_path / 'research_data.sqlite')

    evaluation_id = database.save_pdf_txt_bertscore_evaluation(
        {
            'question_or_theme': 'Quais doses foram mais eficazes?',
            'reference_mode': 'Usar chunks mais relevantes',
            'top_k': 5,
            'txt_file_name': 'resposta_chatbot.txt',
            'txt_encoding': 'utf-8',
            'uploaded_pdfs': [{'file_name': 'artigo_a.pdf'}],
            'reference_text': 'texto de referencia',
            'reference_chunks': [{'chunk_id': '001_chunk_0001'}],
            'candidate_text': 'texto avaliado',
            'bertscore': {
                'precision': 0.81,
                'recall': 0.77,
                'f1': 0.79,
                'precision_percent': 81.0,
                'recall_percent': 77.0,
                'f1_percent': 79.0,
            },
            'status': 'ok',
            'logs': {'note': 'teste pdf txt'},
            'error': None,
        }
    )

    evaluations = database.list_pdf_txt_bertscore_evaluations(limit=5)

    assert evaluation_id > 0
    assert evaluations
    assert evaluations[0]['id'] == evaluation_id
