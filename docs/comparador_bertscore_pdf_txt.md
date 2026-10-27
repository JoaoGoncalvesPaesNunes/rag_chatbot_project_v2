# Comparador BERTScore PDF + TXT

## Objetivo

Esta funcionalidade foi criada para comparar uma resposta em `TXT` contra um conjunto de `PDFs` enviados no proprio Streamlit, sem alterar a base principal do chatbot RAG.

Ela e util para:

- validar respostas geradas por outros chatbots;
- medir aderencia semantica de um texto em relacao aos artigos enviados;
- registrar experimentos no banco SQLite para analise posterior.

## Como funciona

1. O usuario envia um ou mais PDFs.
2. O usuario envia um TXT com a resposta que deseja avaliar.
3. O sistema salva esses arquivos em uma pasta temporaria do comparador.
4. Cada PDF e lido pagina a pagina.
5. O texto e limpo e fragmentado em chunks.
6. Um indice vetorial temporario e criado apenas para essa comparacao.
7. O texto de referencia e montado a partir dos PDFs enviados.
8. O BERTScore e calculado entre o TXT e esse texto de referencia.
9. O resultado e salvo em `pdf_txt_bertscore_evaluations`.

## Modos de referencia

### Usar texto completo dos PDFs

Concatena o texto limpo dos PDFs enviados, respeitando um limite de caracteres para manter o calculo estavel.

### Usar chunks mais relevantes

Cria embeddings temporarios, faz busca vetorial e usa os chunks mais proximos do tema ou pergunta informada.

Se o usuario nao informar tema, o proprio conteudo do TXT passa a ser usado como consulta de apoio.

### Usar concatenacao controlada dos chunks

Monta uma referencia mais curta e rastreavel, com foco nos primeiros chunks selecionados e limite de tamanho.

## Pastas utilizadas

Os arquivos dessa comparacao ficam separados da base principal:

- `data/comparator_uploads/`
- `data/comparator_processed/`
- `data/comparator_vector_store/`

Isso evita sobrescrever:

- `data/raw_pdfs/`
- `data/processed/`
- `data/vector_store/`

## Banco de dados

Tabela criada:

- `pdf_txt_bertscore_evaluations`

Campos principais:

- `id`
- `timestamp`
- `question_or_theme`
- `reference_mode`
- `top_k`
- `txt_file_name`
- `txt_encoding`
- `uploaded_pdfs_json`
- `reference_text`
- `reference_chunks_json`
- `candidate_text`
- `bert_precision`
- `bert_recall`
- `bert_f1`
- `bert_precision_percent`
- `bert_recall_percent`
- `bert_f1_percent`
- `status`
- `logs_json`
- `error`

## O que aparece no Streamlit

Depois do calculo, a interface mostra:

- precision;
- recall;
- F1;
- interpretacao do score;
- PDFs usados;
- trechos usados como referencia;
- texto completo de referencia;
- texto do TXT avaliado;
- ID salvo no banco.

## Como interpretar o resultado

- `F1` alto: o TXT esta semanticamente mais alinhado aos PDFs usados como referencia.
- `F1` medio: existe aderencia parcial, mas pode haver omissoes ou generalizacoes.
- `F1` baixo: a resposta provavelmente se distancia do conteudo dos PDFs ou cobre pouco da evidencia utilizada.

## Limitacoes

1. BERTScore mede proximidade semantica, nao veracidade absoluta.
2. PDFs muito longos podem exigir truncamento do texto de referencia.
3. Se o PDF tiver baixa qualidade de extracao, a comparacao tambem perde qualidade.
4. O comparador nao usa a web nem busca conhecimento externo.
5. O comparador nao substitui a analise humana dos trechos cientificos.

## Resumo tecnico

Arquivos principais envolvidos:

- [app.py](/C:/ProjetoIC/rag_chatbot_project_v2/app.py)
- [src/comparator_pipeline.py](/C:/ProjetoIC/rag_chatbot_project_v2/src/comparator_pipeline.py)
- [src/database.py](/C:/ProjetoIC/rag_chatbot_project_v2/src/database.py)
- [src/evaluation.py](/C:/ProjetoIC/rag_chatbot_project_v2/src/evaluation.py)
