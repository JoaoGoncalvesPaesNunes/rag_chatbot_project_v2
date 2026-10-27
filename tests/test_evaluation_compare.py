from pathlib import Path

from src.evaluation import EvaluationManager


def test_compare_two_answers_with_bertscore_reports_error_for_empty_reference(tmp_path: Path):
    manager = EvaluationManager(tmp_path / 'evaluations.json')

    result = manager.compare_two_answers_with_bertscore(
        fisio_answer='Resposta A',
        other_answer='Resposta B',
        reference_text='',
    )

    assert result['status'] == 'error'
    assert result['winner'] is None
