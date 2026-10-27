# Relatório Técnico Amplo — Arquitetura RAG do Chatbot Acadêmico

## 1. Conceito
RAG (Retrieval-Augmented Generation) é uma arquitetura que combina recuperação de informação com geração de texto por modelos de linguagem. Em vez de depender apenas dos parâmetros internos do modelo, o sistema primeiro recupera trechos relevantes de uma base de conhecimento e, em seguida, condiciona a resposta a esse contexto.

## 2. Motivação
Em chatbots acadêmicos de domínio fechado, a principal preocupação é reduzir alucinações e aumentar a rastreabilidade. Ao usar somente PDFs locais e impor RAG obrigatório, o sistema prioriza respostas verificáveis e evita extrapolações não suportadas.

## 3. Pipeline adotado
1. Ingestão dos PDFs locais.
2. Extração de texto por página.
3. Limpeza do texto.
4. Chunking com overlap.
5. Embeddings locais.
6. Indexação vetorial em FAISS.
7. Recuperação por similaridade.
8. Reranking.
9. Montagem de prompt de domínio fechado.
10. Geração condicionada pela DeepSeek.
11. Avaliação com BERTScore e persistência em logs.

## 4. Vantagens
- Respostas com evidência explícita.
- Redução de alucinações.
- Melhor auditabilidade.
- Independência de internet como base factual do chatbot.
- Facilidade para atualizar a base apenas trocando PDFs.

## 5. Limitações
- Extração de texto de PDFs pode ser imperfeita.
- Chunking afeta diretamente a qualidade da recuperação.
- Similaridade vetorial não substitui julgamento semântico humano.
- A resposta final ainda depende do cumprimento do prompt pelo modelo gerador.

## 6. Papel dos embeddings
Embeddings representam textos em espaço vetorial contínuo. Isso permite comparar semanticamente a pergunta do usuário com os chunks extraídos dos PDFs, mesmo quando as palavras não coincidem exatamente.

## 7. Papel do FAISS
FAISS é o motor de busca vetorial local. Neste projeto, ele armazena embeddings normalizados e realiza busca por produto interno, que, com vetores normalizados, aproxima similaridade de cosseno.

## 8. Papel da recuperação
A recuperação define quais evidências entram no prompt. Em um sistema RAG, a qualidade da resposta depende fortemente da qualidade do contexto recuperado.

## 9. Papel do reranking
Depois da busca vetorial, o reranking reorganiza os resultados com base em um score ponderado entre similaridade vetorial e overlap lexical. Isso ajuda a colocar no topo os contextos mais úteis para a resposta.

## 10. Papel da DeepSeek
A DeepSeek atua como modelo gerador. Ela não é usada como fonte factual primária. Sua função é organizar, explicar e redigir a resposta com base no contexto recuperado.

## 11. Geração condicionada ao contexto
A geração condicionada significa que o modelo recebe instruções explícitas para não usar conhecimento externo e se limitar ao contexto fornecido. Isso é essencial para domínio fechado.

## 12. BERTScore e avaliação
O BERTScore mede proximidade semântica entre resposta e referência. Neste projeto, as referências são os próprios chunks recuperados. A métrica auxilia avaliação de aderência, mas deve ser complementada com inspeção humana.

## 13. Adequação ao contexto de iniciação científica
A arquitetura foi pensada para ser explicável, modular e evolutiva. Isso facilita apresentação acadêmica, replicação de experimentos e futura comparação com outras abordagens.
