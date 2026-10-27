from src.config import Config


def test_paths_exist_after_ensure_directories():
    Config.ensure_directories()
    assert Config.DATA_DIR.exists()
    assert Config.LOGS_DIR.exists()
    assert Config.COMPARATOR_UPLOADS_DIR.exists()
    assert Config.COMPARATOR_PROCESSED_DIR.exists()
    assert Config.COMPARATOR_VECTOR_STORE_DIR.exists()
