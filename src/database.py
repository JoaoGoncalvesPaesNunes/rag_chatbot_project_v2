from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from src.utils import utc_timestamp


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False)


class ResearchDatabase:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA journal_mode=MEMORY')
        connection.execute('PRAGMA synchronous=NORMAL')
        connection.execute('PRAGMA temp_store=MEMORY')
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS chat_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    question TEXT NOT NULL,
                    prompt_profile TEXT,
                    llm_model TEXT,
                    answer TEXT,
                    insufficient_evidence INTEGER NOT NULL DEFAULT 0,
                    retrieved_context_json TEXT,
                    sources_json TEXT,
                    scores_json TEXT,
                    bertscore_json TEXT,
                    error TEXT
                )
                '''
            )
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS bert_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interaction_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    bert_precision REAL,
                    bert_recall REAL,
                    bert_f1 REAL,
                    reference_text TEXT,
                    candidate_text TEXT,
                    status TEXT,
                    logs_json TEXT,
                    FOREIGN KEY (interaction_id) REFERENCES chat_interactions(id)
                )
                '''
            )
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS response_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    base_question TEXT,
                    top_k INTEGER,
                    reference_mode TEXT,
                    reference_text TEXT,
                    reference_chunks_json TEXT,
                    chatbot_fisio_answer TEXT,
                    other_chatbot_answer TEXT,
                    fisio_bert_precision REAL,
                    fisio_bert_recall REAL,
                    fisio_bert_f1 REAL,
                    fisio_bert_precision_percent REAL,
                    fisio_bert_recall_percent REAL,
                    fisio_bert_f1_percent REAL,
                    other_bert_precision REAL,
                    other_bert_recall REAL,
                    other_bert_f1 REAL,
                    other_bert_precision_percent REAL,
                    other_bert_recall_percent REAL,
                    other_bert_f1_percent REAL,
                    winner TEXT,
                    logs_json TEXT,
                    error TEXT
                )
                '''
            )
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS pdf_txt_bertscore_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    question_or_theme TEXT,
                    reference_mode TEXT,
                    top_k INTEGER,
                    txt_file_name TEXT,
                    txt_encoding TEXT,
                    uploaded_pdfs_json TEXT,
                    reference_text TEXT,
                    reference_chunks_json TEXT,
                    candidate_text TEXT,
                    bert_precision REAL,
                    bert_recall REAL,
                    bert_f1 REAL,
                    bert_precision_percent REAL,
                    bert_recall_percent REAL,
                    bert_f1_percent REAL,
                    status TEXT,
                    logs_json TEXT,
                    error TEXT
                )
                '''
            )
            connection.commit()

    def save_interaction(self, payload: Dict) -> int:
        record = dict(payload)
        record.setdefault('timestamp', utc_timestamp())
        with self._connect() as connection:
            cursor = connection.execute(
                '''
                INSERT INTO chat_interactions (
                    timestamp,
                    question,
                    prompt_profile,
                    llm_model,
                    answer,
                    insufficient_evidence,
                    retrieved_context_json,
                    sources_json,
                    scores_json,
                    bertscore_json,
                    error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    record['timestamp'],
                    record.get('question', ''),
                    record.get('prompt_profile'),
                    record.get('llm_model'),
                    record.get('answer'),
                    1 if record.get('insufficient_evidence') else 0,
                    _json_dumps(record.get('retrieved_context', [])),
                    _json_dumps(record.get('sources', [])),
                    _json_dumps(record.get('scores', [])),
                    _json_dumps(record.get('bertscore', {})),
                    record.get('error'),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def save_bert_evaluation(self, interaction_id: int, payload: Dict) -> int:
        record = dict(payload)
        record.setdefault('timestamp', utc_timestamp())
        with self._connect() as connection:
            cursor = connection.execute(
                '''
                INSERT INTO bert_evaluations (
                    interaction_id,
                    timestamp,
                    bert_precision,
                    bert_recall,
                    bert_f1,
                    reference_text,
                    candidate_text,
                    status,
                    logs_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    interaction_id,
                    record['timestamp'],
                    record.get('precision'),
                    record.get('recall'),
                    record.get('f1'),
                    record.get('reference_text'),
                    record.get('candidate_text'),
                    record.get('status'),
                    _json_dumps(record.get('logs', {})),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_interactions(self, limit: int = 20) -> List[Dict]:
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT *
                FROM chat_interactions
                ORDER BY id DESC
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def save_response_comparison(self, payload: Dict) -> int:
        record = dict(payload)
        record.setdefault('timestamp', utc_timestamp())
        fisio = record.get('fisio', {})
        other = record.get('other', {})
        with self._connect() as connection:
            cursor = connection.execute(
                '''
                INSERT INTO response_comparisons (
                    timestamp,
                    base_question,
                    top_k,
                    reference_mode,
                    reference_text,
                    reference_chunks_json,
                    chatbot_fisio_answer,
                    other_chatbot_answer,
                    fisio_bert_precision,
                    fisio_bert_recall,
                    fisio_bert_f1,
                    fisio_bert_precision_percent,
                    fisio_bert_recall_percent,
                    fisio_bert_f1_percent,
                    other_bert_precision,
                    other_bert_recall,
                    other_bert_f1,
                    other_bert_precision_percent,
                    other_bert_recall_percent,
                    other_bert_f1_percent,
                    winner,
                    logs_json,
                    error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    record['timestamp'],
                    record.get('base_question'),
                    record.get('top_k'),
                    record.get('reference_mode'),
                    record.get('reference_text'),
                    _json_dumps(record.get('reference_chunks', [])),
                    record.get('chatbot_fisio_answer'),
                    record.get('other_chatbot_answer'),
                    fisio.get('precision'),
                    fisio.get('recall'),
                    fisio.get('f1'),
                    fisio.get('precision_percent'),
                    fisio.get('recall_percent'),
                    fisio.get('f1_percent'),
                    other.get('precision'),
                    other.get('recall'),
                    other.get('f1'),
                    other.get('precision_percent'),
                    other.get('recall_percent'),
                    other.get('f1_percent'),
                    record.get('winner'),
                    _json_dumps(record.get('logs', {})),
                    record.get('error'),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def save_pdf_txt_bertscore_evaluation(self, payload: Dict) -> int:
        record = dict(payload)
        record.setdefault('timestamp', utc_timestamp())
        bertscore = record.get('bertscore', {})
        with self._connect() as connection:
            cursor = connection.execute(
                '''
                INSERT INTO pdf_txt_bertscore_evaluations (
                    timestamp,
                    question_or_theme,
                    reference_mode,
                    top_k,
                    txt_file_name,
                    txt_encoding,
                    uploaded_pdfs_json,
                    reference_text,
                    reference_chunks_json,
                    candidate_text,
                    bert_precision,
                    bert_recall,
                    bert_f1,
                    bert_precision_percent,
                    bert_recall_percent,
                    bert_f1_percent,
                    status,
                    logs_json,
                    error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    record['timestamp'],
                    record.get('question_or_theme'),
                    record.get('reference_mode'),
                    record.get('top_k'),
                    record.get('txt_file_name'),
                    record.get('txt_encoding'),
                    _json_dumps(record.get('uploaded_pdfs', [])),
                    record.get('reference_text'),
                    _json_dumps(record.get('reference_chunks', [])),
                    record.get('candidate_text'),
                    bertscore.get('precision'),
                    bertscore.get('recall'),
                    bertscore.get('f1'),
                    bertscore.get('precision_percent'),
                    bertscore.get('recall_percent'),
                    bertscore.get('f1_percent'),
                    record.get('status'),
                    _json_dumps(record.get('logs', {})),
                    record.get('error'),
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def list_bert_evaluations(self, limit: int = 20) -> List[Dict]:
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT *
                FROM bert_evaluations
                ORDER BY id DESC
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_response_comparisons(self, limit: int = 20) -> List[Dict]:
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT *
                FROM response_comparisons
                ORDER BY id DESC
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def list_pdf_txt_bertscore_evaluations(self, limit: int = 20) -> List[Dict]:
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT *
                FROM pdf_txt_bertscore_evaluations
                ORDER BY id DESC
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_interaction_by_id(self, interaction_id: int) -> Dict | None:
        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT *
                FROM chat_interactions
                WHERE id = ?
                ''',
                (interaction_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_evaluation_by_interaction_id(self, interaction_id: int) -> Dict | None:
        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT *
                FROM bert_evaluations
                WHERE interaction_id = ?
                ORDER BY id DESC
                LIMIT 1
                ''',
                (interaction_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_response_comparison_by_id(self, comparison_id: int) -> Dict | None:
        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT *
                FROM response_comparisons
                WHERE id = ?
                ''',
                (comparison_id,),
            ).fetchone()
        return dict(row) if row else None

    def get_pdf_txt_bertscore_evaluation_by_id(self, evaluation_id: int) -> Dict | None:
        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT *
                FROM pdf_txt_bertscore_evaluations
                WHERE id = ?
                ''',
                (evaluation_id,),
            ).fetchone()
        return dict(row) if row else None
