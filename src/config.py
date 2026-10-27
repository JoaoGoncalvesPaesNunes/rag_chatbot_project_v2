from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def _env_bool(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {'1', 'true', 'yes', 'on'}


class Config:
    BASE_DIR = BASE_DIR

    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    BERT_SCORE_MODEL = os.getenv('BERT_SCORE_MODEL', 'bert-base-multilingual-cased')
    BERT_SCORE_NUM_LAYERS = int(os.getenv('BERT_SCORE_NUM_LAYERS', '12'))

    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '450'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '80'))
    TOP_K = int(os.getenv('TOP_K', '6'))
    SCORE_THRESHOLD = float(os.getenv('SCORE_THRESHOLD', '0.35'))
    SCORE_FALLBACK_THRESHOLD = float(os.getenv('SCORE_FALLBACK_THRESHOLD', '0.15'))
    DEEPSEEK_TIMEOUT = int(os.getenv('DEEPSEEK_TIMEOUT', '60'))
    RAG_DEBUG = _env_bool('RAG_DEBUG', False)

    DATA_DIR = BASE_DIR / os.getenv('DATA_DIR', 'data')
    RAW_PDFS_DIR = BASE_DIR / os.getenv('RAW_PDFS_DIR', 'data/raw_pdfs')
    PROCESSED_DIR = BASE_DIR / os.getenv('PROCESSED_DIR', 'data/processed')
    VECTOR_STORE_DIR = BASE_DIR / os.getenv('VECTOR_STORE_DIR', 'data/vector_store')
    LOGS_DIR = BASE_DIR / os.getenv('LOGS_DIR', 'logs')
    RESEARCH_LOGS_DIR = DATA_DIR / os.getenv('RESEARCH_LOGS_DIR', 'research_logs')
    COMPARATOR_UPLOADS_DIR = DATA_DIR / os.getenv('COMPARATOR_UPLOADS_DIR', 'comparator_uploads')
    COMPARATOR_PROCESSED_DIR = DATA_DIR / os.getenv('COMPARATOR_PROCESSED_DIR', 'comparator_processed')
    COMPARATOR_VECTOR_STORE_DIR = DATA_DIR / os.getenv('COMPARATOR_VECTOR_STORE_DIR', 'comparator_vector_store')
    SQLITE_DB_PATH = RESEARCH_LOGS_DIR / os.getenv('SQLITE_DB_NAME', 'research_data.sqlite')
    CONVERSATIONS_DIR = LOGS_DIR / 'conversations'
    EVALUATIONS_DIR = LOGS_DIR / 'evaluations'
    REPORTS_DIR = LOGS_DIR / 'reports'

    COMPARATOR_DEFAULT_TOP_K = int(os.getenv('COMPARATOR_DEFAULT_TOP_K', '5'))
    COMPARATOR_REFERENCE_MAX_CHARS = int(os.getenv('COMPARATOR_REFERENCE_MAX_CHARS', '12000'))

    @classmethod
    def ensure_directories(cls) -> None:
        for path in [
            cls.DATA_DIR,
            cls.RAW_PDFS_DIR,
            cls.PROCESSED_DIR,
            cls.VECTOR_STORE_DIR,
            cls.LOGS_DIR,
            cls.RESEARCH_LOGS_DIR,
            cls.COMPARATOR_UPLOADS_DIR,
            cls.COMPARATOR_PROCESSED_DIR,
            cls.COMPARATOR_VECTOR_STORE_DIR,
            cls.CONVERSATIONS_DIR,
            cls.EVALUATIONS_DIR,
            cls.REPORTS_DIR,
        ]:
            path.mkdir(parents=True, exist_ok=True)
