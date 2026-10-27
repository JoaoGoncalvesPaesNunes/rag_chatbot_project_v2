# rag_chatbot_project_v2

Chatbot academico em dominio fechado com RAG sobre PDFs locais, embeddings com `sentence-transformers`, indice vetorial `FAISS`, resposta pela API da DeepSeek, avaliacao automatica com BERTScore, comparador isolado de `PDF + TXT` e persistencia estruturada em SQLite.

## O que o projeto faz

1. Indexa PDFs locais em `data/raw_pdfs/`.
2. Extrai texto pagina a pagina.
3. Tenta identificar titulo cientifico e DOI.
4. Gera chunks com metadados cientificos.
5. Cria embeddings locais e persiste o indice FAISS.
6. Recupera contexto relevante para cada pergunta.
7. Monta prompt de dominio fechado e chama a DeepSeek.
8. Calcula BERTScore com base na resposta e nos trechos recuperados.
9. Salva interacoes em JSON e SQLite.
10. Permite comparar um arquivo TXT contra PDFs enviados na hora, sem sobrescrever a base principal.

## Estrutura principal

```text
rag_chatbot_project_v2/
├── app.py
├── main.py
├── index_pdfs.py
├── debug_rag.py
├── .env.example
├── requirements.txt
├── docs/
│   └── documentacao_fase_2.md
├── data/
│   ├── raw_pdfs/
│   ├── processed/
│   ├── vector_store/
│   └── research_logs/
└── src/
    ├── chatbot.py
    ├── config.py
    ├── metadata_extractor.py
    ├── database.py
    ├── pdf_loader.py
    ├── chunker.py
    ├── retriever.py
    ├── vector_store.py
    ├── prompt_builder.py
    ├── llm_client.py
    ├── evaluation.py
    └── ...
```

Novos diretorios usados pelo comparador PDF + TXT:

- `data/comparator_uploads/`
- `data/comparator_processed/`
- `data/comparator_vector_store/`

Novo modulo principal do comparador:

- `src/comparator_pipeline.py`

## Como rodar no Windows

### 1. Entrar na pasta do projeto

```powershell
cd C:\ProjetoIC\rag_chatbot_project_v2
```

### 2. Criar e ativar o ambiente virtual

```powershell
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar o `.env`

```powershell
Copy-Item .env.example .env
```

Preencha `DEEPSEEK_API_KEY` no arquivo `.env`.

### 5. Colocar PDFs

Adicione os artigos cientificos em:

```text
data/raw_pdfs/
```

### 6. Reindexar a base

```powershell
python .\index_pdfs.py
```

### 7. Rodar no terminal

```powershell
python .\main.py
```

### 8. Rodar no Streamlit

```powershell
streamlit run .\app.py
```

## Banco SQLite

O banco local fica em:

```text
data/research_logs/research_data.sqlite
```

Tabelas principais:

- `chat_interactions`
- `bert_evaluations`
- `response_comparisons`
- `pdf_txt_bertscore_evaluations`

## Aba Comparador BERTScore

No Streamlit, a aba `Comparador BERTScore` permite:

- enviar um ou mais PDFs cientificos temporarios;
- enviar um arquivo TXT com a resposta que sera avaliada;
- escolher entre texto completo, chunks mais relevantes ou concatenacao controlada;
- informar uma pergunta ou tema opcional para ajudar na selecao dos trechos;
- calcular BERTScore sem mexer no FAISS principal do chatbot;
- salvar o resultado no SQLite.

## Diagnostico do pipeline

Para verificar indice, metadados e retrieval:

```powershell
python .\debug_rag.py --query laser
python .\debug_rag.py --query "dor lombar"
```

## Documentacao tecnica

Veja a documentacao detalhada em:

[docs/documentacao_fase_2.md](/C:/ProjetoIC/rag_chatbot_project_v2/docs/documentacao_fase_2.md)
[docs/comparador_respostas.md](/C:/ProjetoIC/rag_chatbot_project_v2/docs/comparador_respostas.md)
[docs/comparador_bertscore_pdf_txt.md](/C:/ProjetoIC/rag_chatbot_project_v2/docs/comparador_bertscore_pdf_txt.md)
