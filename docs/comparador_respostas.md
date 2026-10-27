# Comparador de Respostas

> Observacao: este documento descreve o comparador antigo de duas respostas coladas manualmente. A interface atual do Streamlit prioriza o comparador `PDF + TXT`, descrito em [docs/comparador_bertscore_pdf_txt.md](/C:/ProjetoIC/rag_chatbot_project_v2/docs/comparador_bertscore_pdf_txt.md).

## Objetivo

A aba `Comparador de Respostas` foi criada para comparar manualmente duas respostas de chatbots diferentes com base nos textos cientificos locais do projeto.

Ela nao substitui o chatbot principal. Ela funciona como uma ferramenta adicional de avaliacao.

## Como funciona

O usuario cola manualmente:

1. a resposta do `Chatbot Fisio`;
2. a resposta de `Outro Chatbot`.

Depois escolhe como o texto de referencia sera montado:

- `Recuperar Top-K por pergunta`
- `Usar todos os chunks indexados`
- `Colar texto de referencia manual`

O modo recomendado e `Recuperar Top-K por pergunta`, porque ele compara as respostas com os trechos mais relevantes dos PDFs.

## Pergunta-base

Quando a pergunta-base e informada, o sistema:

1. consulta o indice FAISS;
2. recupera os chunks mais proximos da pergunta;
3. concatena esses chunks;
4. usa esse texto como referencia do BERTScore.

Isso torna a comparacao mais justa e mais interpretavel do que comparar contra toda a base ao mesmo tempo.

## O que o sistema calcula

Para cada resposta, o sistema calcula:

- `Precision`
- `Recall`
- `F1`

Tambem exibe as mesmas metricas em porcentagem.

O score principal de comparacao e o `BERTScore F1`.

## Como interpretar

### Precision

Indica o quanto a resposta se aproxima semanticamente do texto de referencia sem introduzir excesso de conteudo fora da base.

### Recall

Indica o quanto da informacao presente na referencia parece ter sido coberta pela resposta.

### F1

Resume Precision e Recall em um unico indicador.

Na pratica, o `F1` e o melhor numero para comparar as duas respostas.

## Resultado esperado

Depois de clicar em `Comparar respostas`, o sistema mostra:

- score da resposta do Chatbot Fisio;
- score da resposta do Outro Chatbot;
- vencedor da comparacao;
- trechos dos PDFs usados como referencia;
- texto completo de referencia em expander;
- ID da comparacao salva no banco.

## Banco de dados

As comparacoes ficam salvas em:

```text
data/research_logs/research_data.sqlite
```

Tabela:

- `response_comparisons`

Campos importantes:

- `base_question`
- `top_k`
- `reference_mode`
- `reference_text`
- `reference_chunks_json`
- `chatbot_fisio_answer`
- `other_chatbot_answer`
- `fisio_bert_f1`
- `other_bert_f1`
- `winner`
- `logs_json`

## Limitacoes

1. O BERTScore mede aderencia semantica, nao veracidade absoluta.
2. Comparar contra todos os chunks pode deixar o resultado menos interpretavel.
3. Se a pergunta-base recuperar chunks ruins, a comparacao tambem sera prejudicada.
4. O calculo depende do modelo local do BERTScore; se ele falhar, a interface mostra erro amigavel.

## Recomendações de uso

1. Use a mesma pergunta-base que originou as respostas.
2. Comece com `Top-K = 5`.
3. Compare respostas sobre temas realmente presentes nos PDFs.
4. Verifique sempre os trechos de referencia exibidos.

## Exemplo de uso

Pergunta-base:

```text
Quais sao os efeitos da fotobiomodulacao na dor lombar?
```

Resposta do Chatbot Fisio:

```text
[cole aqui a resposta gerada]
```

Resposta de Outro Chatbot:

```text
[cole aqui a outra resposta]
```

Depois compare os valores de `F1` e leia a conclusao exibida pelo sistema.
