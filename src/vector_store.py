from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import faiss
import numpy as np


class VectorStore:
    def __init__(self, dimension: int):
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.metadata: List[Dict] = []
        self.manifest: Dict[str, Any] = {}

    def add(self, vectors: np.ndarray, metadata: List[Dict]) -> None:
        if len(vectors) == 0:
            return
        if len(vectors) != len(metadata):
            raise ValueError(
                'Quantidade de vetores diferente da quantidade de metadados: '
                f'vectors={len(vectors)} metadata={len(metadata)}'
            )
        self.index.add(vectors)
        self.metadata.extend(metadata)

    def save(self, directory: str | Path, embedding_model: str | None = None) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(directory / 'faiss.index'))
        with (directory / 'index_metadata.json').open('w', encoding='utf-8') as file:
            json.dump(self.metadata, file, ensure_ascii=False, indent=2)

        self.manifest = {
            'embedding_model': embedding_model,
            'dimension': self.index.d,
            'vector_count': self.index.ntotal,
            'metadata_count': len(self.metadata),
        }
        with (directory / 'index_manifest.json').open('w', encoding='utf-8') as file:
            json.dump(self.manifest, file, ensure_ascii=False, indent=2)

    def load(self, directory: str | Path) -> None:
        directory = Path(directory)
        self.index = faiss.read_index(str(directory / 'faiss.index'))
        with (directory / 'index_metadata.json').open('r', encoding='utf-8') as file:
            self.metadata = json.load(file)

        manifest_path = directory / 'index_manifest.json'
        if manifest_path.exists():
            with manifest_path.open('r', encoding='utf-8') as file:
                self.manifest = json.load(file)
        else:
            self.manifest = {}

    def exists(self, directory: str | Path) -> bool:
        directory = Path(directory)
        return (directory / 'faiss.index').exists() and (directory / 'index_metadata.json').exists()

    def validate(self) -> None:
        if self.index.ntotal != len(self.metadata):
            raise ValueError(
                'Inconsistencia critica no indice vetorial: '
                f'faiss.ntotal={self.index.ntotal} metadata={len(self.metadata)}'
            )
        if self.index.d != self.dimension:
            raise ValueError(
                'Dimensao inconsistente no indice vetorial: '
                f'index.d={self.index.d} vector_store.dimension={self.dimension}'
            )
        manifest_vectors = self.manifest.get('vector_count')
        if manifest_vectors is not None and manifest_vectors != self.index.ntotal:
            raise ValueError(
                'Manifesto inconsistente com o indice vetorial: '
                f'manifest.vector_count={manifest_vectors} faiss.ntotal={self.index.ntotal}'
            )

    def stats(self) -> Dict[str, Any]:
        return {
            'vector_count': self.index.ntotal,
            'dimension': self.index.d,
            'metadata_count': len(self.metadata),
            'manifest': self.manifest,
        }

    def search(self, query_vector: np.ndarray, top_k: int) -> List[Dict]:
        if self.index.ntotal == 0:
            return []
        scores, indices = self.index.search(query_vector, top_k)
        results: List[Dict] = []
        for idx, score in zip(indices[0], scores[0]):
            if idx == -1:
                continue
            results.append(
                {
                    'vector_score': float(score),
                    'metadata': self.metadata[idx],
                }
            )
        return results
