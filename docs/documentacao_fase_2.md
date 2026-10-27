# Documentacao Tecnica da Fase 2

## Objetivo

Esta fase evolui o `rag_chatbot_project_v2` sem quebrar o fluxo anterior. O foco foi aumentar rastreabilidade cientifica, capacidade de avaliacao e persistencia estruturada.

Os objetivos implementados foram:

1. Integrar calculo real de BERTScore ao fluxo do chatbot.
2. Substituir referencias cruas de PDF por titulo cientifico e DOI quando possivel.
3. Persistir interacoes e avaliacoes em SQLite, preservando os logs JSON existentes.
4. Melhorar o diagnostico do pipeline RAG.

## Arquitetura Geral

Fluxo atualizado:

1. PDFs locais sao lidos de `data/raw_pdfs/`.
2. `src/pdf_loader.py` extrai texto pagina a pagina.
3. `src/metadata_extractor.py` tenta identificar titulo, DOI e referencia amigavel.
4. `src/chunker.py` cria chunks com texto e metadados cientificos.
5. `src/embeddings.py` gera embeddings locais com `sentence-transformers`.
6. `src/vector_store.py` persiste vetores e metadados em FAISS + JSON.
7. `src/retriever.py` busca os chunks mais similares por score vetorial.
8. `src/reranker.py` combina score vetorial com overlap lexical.
9. `src/prompt_builder.py` monta um prompt restrito ao contexto recuperado.
10. `src/llm_client.py` chama a DeepSeek somente para geracao final.
11. `src/evaluation.py` calcula BERTScore entre resposta e contexto recuperado.
12. `src/database.py` salva a interacao e a avaliacao no SQLite.
13. `app.py` e `main.py` exibem resposta, fontes, score e IDs persistidos.

## Modulos adicionados ou alterados

### `src/metadata_extractor.py`

Responsavel por:

- detectar DOI via regex;
- inspecionar as primeiras linhas das primeiras paginas;
- escolher um titulo provavel;
- criar `display_reference`;
- aplicar fallback seguro quando metadados nao forem encontrados.

Saida padrao:

```json
{
  "pdf_name": "artigo.pdf",
  "title": "Titulo identificado",
  "doi": "10.xxxx/xxxx",
  "display_reference": "Titulo identificado. DOI: 10.xxxx/xxxx"
}
```

### `src/database.py`

Cria e gerencia o banco SQLite em:

```text
data/research_logs/research_data.sqlite
```

Tabelas:

#### `chat_interactions`

- `id`
- `timestamp`
- `question`
- `prompt_profile`
- `llm_model`
- `answer`
- `insufficient_evidence`
- `retrieved_context_json`
- `sources_json`
- `scores_json`
- `bertscore_json`
- `error`

#### `bert_evaluations`

- `id`
- `interaction_id`
- `timestamp`
- `bert_precision`
- `bert_recall`
- `bert_f1`
- `reference_text`
- `candidate_text`
- `status`
- `logs_json`

### `src/evaluation.py`

O calculo do BERTScore agora faz parte do fluxo real do chatbot.

Entradas:

- resposta gerada;
- chunks recuperados;
- pergunta original;
- metadados das fontes.

Saida:

- `status`
- `precision`
- `recall`
- `f1`
- `note`
- `reference_text`
- `candidate_text`
- `logs`

Se o pacote `bert-score` ou o modelo nao estiverem disponiveis, o sistema retorna fallback estruturado com status `unavailable`, sem quebrar a interacao.

### `src/pdf_loader.py`

Agora retorna:

- texto bruto por pagina;
- texto limpo por pagina;
- metadados cientificos extraidos;
- texto completo limpo do documento.

### `src/chunker.py`

Cada chunk passou a carregar:

- `chunk_id`
- `text`
- `pdf_name`
- `title`
- `doi`
- `display_reference`
- `page_start`
- `page_end`
- `position_start_word`
- `position_end_word`
- `document_position`

### `src/vector_store.py`

Novas validacoes:

- numero de vetores igual ao numero de metadados;
- manifesto com `vector_count` e `metadata_count`;
- erro explicito em caso de inconsistencias.

### `src/retriever.py`

Melhorias:

- retorno com `retrieval_mode`;
- debug mais rico;
- metadados cientificos preservados nos resultados.

### `src/prompt_builder.py`

O prompt agora instrui explicitamente o modelo a:

- responder apenas com base no contexto recuperado;
- nao usar conhecimento externo;
- citar titulo e DOI quando possivel;
- declarar limitacoes da base.

### `src/chatbot.py`

Fluxo final:

1. recebe a pergunta;
2. recupera os chunks;
3. interrompe a chamada ao LLM se nao houver contexto;
4. gera a resposta com a DeepSeek;
5. calcula BERTScore;
6. salva JSON e SQLite;
7. retorna resposta, fontes, scores, BERTScore e IDs persistidos.

### `app.py`

A interface Streamlit agora exibe:

- resposta;
- BERTScore;
- ID da interacao;
- ID da avaliacao;
- fontes com titulo, DOI, paginas e chunk;
- score por chunk;
- contexto recuperado em expanders;
- painel lateral com base indexada;
- botao para reindexar PDFs.

### `debug_rag.py`

O script de diagnostico agora:

1. lista os PDFs brutos;
2. lista os arquivos do vetor store;
3. carrega o indice;
4. mostra a quantidade de vetores;
5. mostra a quantidade de metadados;
6. imprime os tres primeiros metadados;
7. testa uma busca simples;
8. mostra chunks recuperados;
9. informa onde o pipeline falha.

## Extracao de texto dos PDFs

Fluxo:

1. tentativa com `PyMuPDF`;
2. fallback para `pypdf`;
3. limpeza textual em `src/text_cleaner.py`.

Saidas persistidas por PDF:

- `cleaned_text.json`
- `chunks.json`
- `metadata.json`

## Limpeza textual

As regras atuais incluem:

- juncao de palavras quebradas por hifen;
- normalizacao de quebras de linha;
- remocao de caracteres de controle;
- compressao de espacos repetidos;
- reducao de linhas vazias excessivas.

## Embeddings e FAISS

Modelo padrao:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

O FAISS utiliza `IndexFlatIP` sobre embeddings normalizados, o que aproxima similaridade de cosseno.

Arquivos persistidos:

- `data/vector_store/faiss.index`
- `data/vector_store/index_metadata.json`
- `data/vector_store/index_manifest.json`

## BERTScore

Modelo padrao:

```text
bert-base-multilingual-cased
```

Comparacao utilizada:

- candidato: resposta final do chatbot;
- referencia: concatenacao dos trechos recuperados do RAG.

Importante:

- o BERTScore nao mede veracidade sozinho;
- ele ajuda a estimar aderencia semantica entre resposta e contexto recuperado;
- em ambiente sem cache do modelo, a primeira execucao pode falhar e cair no fallback estruturado.

## Como rodar

### Preparacao

```powershell
cd C:\ProjetoIC\rag_chatbot_project_v2
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Preencha `DEEPSEEK_API_KEY` no `.env`.

### Indexacao

```powershell
python .\index_pdfs.py
```

### CLI

```powershell
python .\main.py
```

### Streamlit

```powershell
streamlit run .\app.py
```

### Debug

```powershell
python .\debug_rag.py --query laser
```

## Como interpretar os resultados

### Quando houver contexto recuperado

Voce deve ver:

- resposta baseada nos PDFs;
- lista de fontes com referencia amigavel;
- DOI quando existir;
- paginas e chunk;
- score de recuperacao;
- BERTScore;
- IDs persistidos no banco.

### Quando nao houver contexto

O sistema deve:

- informar falta de evidencia suficiente;
- nao chamar a DeepSeek desnecessariamente;
- salvar a interacao com `insufficient_evidence = 1`;
- registrar BERTScore como `not_run`.

## Problemas comuns

### `faiss.index` ausente

Rode:

```powershell
python .\index_pdfs.py
```

### Nenhum chunk recuperado

Verifique:

- se os PDFs tem texto extraivel;
- se `index_metadata.json` nao esta vazio;
- se o modelo de embeddings do indice e o do `.env` sao os mesmos;
- se os thresholds nao estao altos demais.

### BERTScore indisponivel

Possiveis causas:

- pacote nao instalado corretamente;
- modelo sem cache local;
- falta de internet na primeira carga do modelo.

O sistema nao quebra, mas salva status `unavailable`.

## Limitacoes conhecidas

1. A extracao de titulo e DOI e heuristica, nao perfeita.
2. PDFs escaneados sem OCR podem gerar chunks pobres.
3. O BERTScore depende de modelo Transformer local ou cacheado.
4. O reranker atual continua simples e lexical.
5. O SQLite guarda JSON serializado em algumas colunas para manter o projeto leve e portavel.

## Proximos passos sugeridos

1. Adicionar testes automatizados para `metadata_extractor` e `database`.
2. Melhorar a extracao de metadados com cruzamento entre paginas.
3. Criar uma tela Streamlit para consulta historica ao SQLite.
4. Adicionar reranking com cross-encoder.
5. Criar metricas agregadas a partir do banco local para a pesquisa.
