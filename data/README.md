# Dados locais

Esta pasta armazena dados gerados ou utilizados localmente. Para proteger os
artigos e as informacoes de pesquisa, os conteudos gerados nao sao enviados ao
GitHub.

## Onde colocar os PDFs

Coloque os artigos cientificos em [`raw_pdfs/`](raw_pdfs/). Em seguida, execute:

```powershell
.\venv\Scripts\python.exe index_pdfs.py
```

O comando cria localmente as pastas de processamento, o indice FAISS e os
metadados necessarios para o chatbot.

## Dados criados automaticamente

- `processed/`: chunks e metadados extraidos dos PDFs.
- `vector_store/`: indice FAISS e metadados da busca vetorial.
- `research_logs/`: banco SQLite com perguntas, respostas e BERTScore.
- `comparator_*`: arquivos temporarios do comparador de BERTScore.

Esses arquivos permanecem neste computador e nao devem ser publicados.
