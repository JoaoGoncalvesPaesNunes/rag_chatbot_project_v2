from pathlib import Path

from src.metadata_extractor import extract_scientific_metadata


def test_extract_scientific_metadata_detects_title_and_doi():
    pages = [
        {
            'page_number': 1,
            'raw_text': '\n'.join(
                [
                    'Effectiveness of photobiomodulation therapy in chronic low back pain',
                    'DOI: 10.1234/example.2026.001',
                    'Abstract',
                ]
            ),
            'cleaned_text': '',
        }
    ]

    metadata = extract_scientific_metadata(Path('sample_article.pdf'), pages)

    assert metadata['title'].startswith('Effectiveness of photobiomodulation therapy')
    assert metadata['doi'] == '10.1234/example.2026.001'
    assert 'DOI:' in metadata['display_reference']
