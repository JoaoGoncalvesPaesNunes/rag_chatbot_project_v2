from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

from src.utils import read_json, utc_timestamp, write_json


def _format_source_labels(sources: List) -> str:
    labels: List[str] = []
    for item in sources or []:
        if isinstance(item, str):
            labels.append(item)
            continue
        if isinstance(item, dict):
            labels.append(item.get('display_reference') or item.get('title') or item.get('pdf_name') or 'fonte')
    return '; '.join(labels)


class ReportGenerator:
    def __init__(self, conversations_path: Path, evaluations_path: Path, reports_dir: Path):
        self.conversations_path = conversations_path
        self.evaluations_path = evaluations_path
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def build_summary(self) -> Dict:
        conversations = read_json(self.conversations_path, default=[])
        evaluations = read_json(self.evaluations_path, default=[])
        bertscores = [item.get('bertscore', {}).get('f1', 0.0) for item in conversations if item.get('bertscore')]
        avg_bert = sum(bertscores) / len(bertscores) if bertscores else 0.0
        insufficient = sum(1 for item in conversations if item.get('insufficient_evidence'))
        return {
            'generated_at': utc_timestamp(),
            'total_interactions': len(conversations),
            'total_evaluations': len(evaluations),
            'average_bertscore_f1': round(avg_bert, 4),
            'insufficient_evidence_count': insufficient,
        }

    def export(self) -> Dict:
        summary = self.build_summary()
        summary_path = self.reports_dir / 'summary_report.json'
        write_json(summary_path, summary)

        conversations = read_json(self.conversations_path, default=[])
        csv_path = self.reports_dir / 'interactions_report.csv'
        with csv_path.open('w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    'timestamp',
                    'question',
                    'prompt_profile',
                    'model',
                    'insufficient_evidence',
                    'bertscore_f1',
                    'sources',
                    'interaction_id',
                ],
            )
            writer.writeheader()
            for item in conversations:
                writer.writerow(
                    {
                        'timestamp': item.get('timestamp'),
                        'question': item.get('question'),
                        'prompt_profile': item.get('prompt_profile'),
                        'model': item.get('model'),
                        'insufficient_evidence': item.get('insufficient_evidence'),
                        'bertscore_f1': item.get('bertscore', {}).get('f1', 0.0),
                        'sources': _format_source_labels(item.get('sources', [])),
                        'interaction_id': item.get('interaction_id'),
                    }
                )
        return {'summary_json': str(summary_path), 'csv_report': str(csv_path), 'summary': summary}
