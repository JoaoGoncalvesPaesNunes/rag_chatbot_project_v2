from __future__ import annotations

from src.config import Config
from src.report_generator import ReportGenerator


def main() -> None:
    Config.ensure_directories()
    generator = ReportGenerator(
        Config.CONVERSATIONS_DIR / 'history.json',
        Config.EVALUATIONS_DIR / 'evaluations.json',
        Config.REPORTS_DIR,
    )
    result = generator.export()
    print('Relatórios gerados com sucesso:')
    print(result)


if __name__ == '__main__':
    main()
