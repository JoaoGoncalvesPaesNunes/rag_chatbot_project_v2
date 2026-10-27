# Como Rodar o Projeto `rag_chatbot_project_v2` no Windows

## 1. Introdução

O projeto `rag_chatbot_project_v2` é um chatbot local em Python baseado em arquitetura RAG, sigla para `Retrieval-Augmented Generation`.

Na prática, isso significa que o sistema:

1. lê PDFs locais;
2. extrai e organiza o texto desses PDFs;
3. transforma os trechos em embeddings;
4. indexa esses embeddings com FAISS;
5. recupera os trechos mais relevantes para uma pergunta;
6. usa a API da DeepSeek para redigir a resposta com base no contexto recuperado.

Este projeto funciona em domínio fechado. Isso quer dizer que a qualidade da resposta depende diretamente da base de PDFs indexada no seu computador.

Ponto importante: antes de consultar o chatbot, você precisa indexar os PDFs. Sem a indexação, o sistema não terá contexto para recuperar e responder.

Resumo do fluxo correto:

1. preparar ambiente;
2. configurar `.env`;
3. colocar os PDFs em `data/raw_pdfs/`;
4. rodar `index_pdfs.py`;
5. rodar `main.py` ou `app.py`.

---

## 2. Estrutura de Pastas do Projeto

Estrutura principal esperada:

```text
rag_chatbot_project_v2/
├── .env
├── .env.example
├── app.py
├── main.py
├── index_pdfs.py
├── debug_rag.py
├── run_reports.py
├── requirements.txt
├── README.md
├── technical_report_rag.md
├── src/
├── data/
│   ├── raw_pdfs/
│   ├── processed/
│   └── vector_store/
├── logs/
│   ├── conversations/
│   ├── evaluations/
│   └── reports/
├── tests/
└── venv/
```

### Função de cada pasta principal

`src/`

- Contém o código-fonte principal do projeto.
- Aqui ficam os módulos de configuração, leitura de PDF, chunking, embeddings, FAISS, retrieval, prompt, cliente da DeepSeek e avaliação.

`data/raw_pdfs/`

- É a pasta onde você deve colocar os PDFs originais.
- O sistema só indexa arquivos `.pdf` encontrados aqui.

`data/processed/`

- Guarda os arquivos intermediários gerados durante a indexação.
- Normalmente surgem pastas por documento contendo:
  - `cleaned_text.json`
  - `chunks.json`
  - `metadata.json`

`data/vector_store/`

- Guarda o índice vetorial final e seus metadados.
- Aqui surgem arquivos como:
  - `faiss.index`
  - `index_metadata.json`
  - `index_manifest.json`

`logs/`

- Guarda o histórico de uso e avaliação do chatbot.
- Subpastas:
  - `logs/conversations/`
  - `logs/evaluations/`
  - `logs/reports/`

### Onde os PDFs devem ser colocados

Os PDFs devem ser colocados exclusivamente em:

```text
data/raw_pdfs/
```

O sistema não busca PDFs automaticamente em outras pastas do computador.

---

## 3. Escolha do Caminho no Windows

Esta etapa é extremamente importante.

Evite deixar o projeto em caminhos com:

- acentos;
- caracteres especiais;
- espaços excessivos;
- nomes muito longos;
- OneDrive;
- diretórios sincronizados automaticamente.

### Por que isso importa

Bibliotecas como FAISS, ambientes virtuais, bibliotecas nativas de Python e até o próprio Streamlit podem apresentar comportamento instável quando o projeto está em caminhos problemáticos.

Problemas típicos:

- falha ao salvar ou carregar `faiss.index`;
- caminhos quebrados em bibliotecas nativas;
- lentidão ou bloqueios por sincronização do OneDrive;
- erro com permissões;
- falha de leitura de arquivos;
- nomes de caminho grandes demais para algumas operações no Windows.

### Exemplo de caminho ruim

```text
C:\Users\NUNES\OneDrive\Documentos\Iniciação Científica CHATBOT\rag_chatbot_project_v2
```

Esse tipo de caminho é ruim porque mistura:

- OneDrive;
- acentuação;
- espaço em excesso;
- nome longo.

### Exemplo de caminho bom

```text
C:\ProjetoIC\rag_chatbot_project_v2
```

Esse caminho é melhor porque:

- é curto;
- não tem acento;
- não está em pasta sincronizada;
- reduz chance de erro com FAISS e com o ambiente virtual.

### Recomendação prática

Se possível, mantenha o projeto exatamente em um caminho como:

```text
C:\ProjetoIC\rag_chatbot_project_v2
```

---

## 4. Criação e Ativação do Ambiente Virtual

### Como abrir o terminal

Você pode usar:

- PowerShell;
- Prompt de Comando (`cmd`);
- Terminal do VS Code.

No Windows, o PowerShell costuma ser a opção mais comum.

### Como entrar na pasta do projeto

No terminal:

```powershell
cd C:\ProjetoIC\rag_chatbot_project_v2
```

### Como criar o ambiente virtual

Se a pasta `venv` ainda não existir:

```powershell
python -m venv venv
```

Isso cria um ambiente virtual isolado dentro da pasta do projeto.

### Como ativar no CMD

Se você estiver usando Prompt de Comando:

```cmd
venv\Scripts\activate.bat
```

### Como ativar no PowerShell

Se você estiver usando PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### Erro comum no PowerShell

É muito comum aparecer erro informando que a execução de scripts está bloqueada.

Exemplo típico:

```text
running scripts is disabled on this system
```

### Como resolver

Execute:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Depois tente ativar novamente:

```powershell
.\venv\Scripts\Activate.ps1
```

### Como saber que o ambiente virtual está ativo

Você normalmente verá algo assim no terminal:

```text
(venv) PS C:\ProjetoIC\rag_chatbot_project_v2>
```

Se o `(venv)` aparecer, o ambiente está ativo.

---

## 5. Instalação de Dependências

Depois de ativar o `venv`, atualize o `pip`:

```powershell
python -m pip install --upgrade pip
```

Depois instale as dependências do projeto:

```powershell
pip install -r requirements.txt
```

### Por que isso é importante

O projeto depende de bibliotecas específicas, como:

- `streamlit`
- `faiss-cpu`
- `sentence-transformers`
- `python-dotenv`
- `PyMuPDF`
- `pypdf`
- `requests`
- `bert-score`

### Regra importante

O projeto deve ser executado com o Python do próprio `venv`.

Evite rodar o projeto com:

- Miniconda;
- Anaconda;
- Python global do Windows;
- outro Python instalado fora do projeto.

### Como conferir qual Python está sendo usado

No PowerShell:

```powershell
python -c "import sys; print(sys.executable)"
```

O caminho ideal deve apontar para algo como:

```text
C:\ProjetoIC\rag_chatbot_project_v2\venv\Scripts\python.exe
```

Se aparecer um Python global, o `venv` não está sendo usado corretamente.

---

## 6. Configuração do `.env`

O projeto usa um arquivo `.env` para centralizar configurações.

### Como criar o `.env`

Se ainda não existir:

```powershell
Copy-Item .env.example .env
```

Depois edite o arquivo `.env`.

### Campos mais importantes

Exemplo:

```env
DEEPSEEK_API_KEY=sua_chave_aqui
DEEPSEEK_MODEL=deepseek-chat
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
CHUNK_SIZE=450
CHUNK_OVERLAP=80
TOP_K=6
SCORE_THRESHOLD=0.35
SCORE_FALLBACK_THRESHOLD=0.15
DEEPSEEK_TIMEOUT=60
RAG_DEBUG=false
```

### Explicação dos campos

`DEEPSEEK_API_KEY`

- Sua chave da API da DeepSeek.
- Sem essa chave, o modelo não consegue gerar respostas.

`DEEPSEEK_MODEL`

- Modelo usado na geração.
- Exemplo padrão:
  - `deepseek-chat`

`EMBEDDING_MODEL`

- Modelo usado para gerar embeddings dos chunks e das perguntas.
- No estado atual do projeto, o recomendado é:
  - `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Observação importante:

- Algumas descrições antigas do projeto podem citar `sentence-transformers/all-MiniLM-L6-v2`.
- Como o uso real envolve perguntas em português e PDFs que podem estar em inglês, o modelo multilíngue é mais seguro.

`CHUNK_SIZE` e `CHUNK_OVERLAP`

- Controlam o tamanho dos chunks e o quanto um bloco sobrepõe o seguinte.

`TOP_K`

- Quantos resultados o sistema tenta recuperar.

`SCORE_THRESHOLD`

- Limiar principal de score para aceitar chunks no retrieval.

`SCORE_FALLBACK_THRESHOLD`

- Limiar secundário de fallback.
- Ajuda quando o threshold principal está agressivo demais.

`RAG_DEBUG`

- Se `true`, imprime informações detalhadas do retrieval.
- Muito útil para depuração.

### O que acontece se a chave estiver ausente ou inválida

Se `DEEPSEEK_API_KEY` estiver vazia:

- a indexação pode até funcionar;
- mas a geração de resposta falhará quando o chatbot tentar consultar a API.

Se a chave estiver inválida:

- a chamada HTTP para a DeepSeek retornará erro;
- o chatbot não conseguirá produzir resposta gerada corretamente.

---

## 7. Preparação das Pastas de Dados

O projeto costuma criar diretórios automaticamente, mas é importante saber quais são e para que servem.

Pastas principais de dados:

```text
data/
data/raw_pdfs/
data/processed/
data/vector_store/
```

### Para que serve cada uma

`data/`

- Pasta principal de dados do projeto.

`data/raw_pdfs/`

- PDFs originais que serão indexados.

`data/processed/`

- Resultado da extração e chunking por documento.

`data/vector_store/`

- Índice FAISS final e metadados do índice.

### Se as pastas não existirem

Você pode criá-las manualmente:

```powershell
mkdir data
mkdir data\raw_pdfs
mkdir data\processed
mkdir data\vector_store
```

---

## 8. Adição dos PDFs

Os PDFs devem ser colocados exclusivamente em:

```text
data/raw_pdfs/
```

Exemplo:

```text
C:\ProjetoIC\rag_chatbot_project_v2\data\raw_pdfs\meu_artigo.pdf
```

### Regras práticas

- use arquivos `.pdf`;
- prefira PDFs com texto selecionável;
- evite depender de PDFs só em imagem se o projeto não tiver OCR;
- mantenha nomes razoáveis de arquivos.

### Importante

O sistema não procura PDFs:

- na área de trabalho;
- em Downloads;
- em Documentos;
- em outra pasta externa.

Se o PDF não estiver em `data/raw_pdfs/`, ele não será indexado.

---

## 9. Indexação dos PDFs

### Comando para indexar

Com o `venv` ativado:

```powershell
python .\index_pdfs.py
```

### O que esse script faz

O script `index_pdfs.py` executa o pipeline de ingestão:

1. lê os PDFs de `data/raw_pdfs/`;
2. extrai o texto de cada página;
3. limpa o texto;
4. divide o conteúdo em chunks;
5. gera embeddings dos chunks;
6. cria o índice vetorial FAISS;
7. salva metadados alinhados ao índice.

### Arquivos esperados após a indexação

Para cada PDF em `data/processed/<nome_do_pdf>/`:

- `cleaned_text.json`
- `chunks.json`
- `metadata.json`

Na pasta `data/vector_store/`:

- `faiss.index`
- `index_metadata.json`
- `index_manifest.json`

### Como verificar se a indexação funcionou

Sinais positivos:

- `faiss.index` existe;
- `index_metadata.json` existe;
- `index_metadata.json` não está vazio;
- `data/processed/` contém pastas e arquivos JSON por documento.

### Observação importante sobre metadados

Algumas instruções antigas podem mencionar `metadata.pkl`.

No estado atual deste projeto, o arquivo correto de metadados do índice é:

```text
data/vector_store/index_metadata.json
```

Além disso, agora existe também:

```text
data/vector_store/index_manifest.json
```

Esse manifesto ajuda a registrar qual modelo de embeddings foi usado na indexação.

---

## 10. Execução no Terminal

Depois da indexação, você pode rodar o chatbot no terminal.

### Comando

```powershell
python .\main.py
```

### Fluxo de uso

O programa vai:

- iniciar o chatbot;
- carregar o índice vetorial;
- esperar uma pergunta;
- opcionalmente permitir escolha do perfil de prompt;
- mostrar resposta, BERTScore e fontes.

### Como usar

1. Digite sua pergunta.
2. Pressione Enter.
3. Informe o perfil de prompt ou pressione Enter para o padrão.
4. Leia a resposta e as fontes.

### Como encerrar

Digite:

```text
sair
```

ou:

```text
exit
```

ou:

```text
quit
```

---

## 11. Execução no Streamlit

Se você quiser usar interface web local:

```powershell
streamlit run .\app.py
```

### O que acontece

O Streamlit inicia um servidor local e normalmente mostra no terminal um endereço parecido com:

```text
http://localhost:8501
```

### Como abrir

- em muitos casos o navegador abre sozinho;
- se não abrir, copie o endereço e cole manualmente no navegador.

### O que a interface mostra

- caixa de pergunta;
- seleção de perfil de prompt;
- resposta do chatbot;
- BERTScore;
- trechos recuperados;
- histórico da sessão.

---

## 12. Testes Recomendados

Depois que o sistema estiver rodando, faça testes simples e controlados.

### Teste 1: pergunta claramente presente no PDF

Exemplo:

- um termo específico do artigo;
- nome de intervenção;
- nome de condição clínica;
- trecho que você sabe que existe nos PDFs.

Comportamento esperado:

- o chatbot deve recuperar contexto;
- deve mostrar trechos ou fontes relacionadas;
- não deve cair imediatamente em “não encontrei evidência suficiente”.

### Teste 2: pergunta parcialmente relacionada

Exemplo:

- uma pergunta com linguagem mais natural, mas ainda dentro do domínio do PDF.

Comportamento esperado:

- o sistema pode recuperar menos contexto;
- ainda assim deve tentar responder se houver evidência.

### Teste 3: pergunta fora da base

Exemplo:

- assunto que não existe nos PDFs.

Comportamento esperado:

- o sistema deve indicar falta de evidência;
- isso é desejado em um RAG de domínio fechado.

---

## 13. Erros Mais Comuns e Soluções

### 13.1 PowerShell bloqueando `Activate.ps1`

Erro típico:

```text
running scripts is disabled on this system
```

Solução:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

---

### 13.2 Uso de Miniconda ou Python global em vez do `venv`

Sintoma:

- dependências parecem instaladas, mas o projeto acusa módulo ausente;
- `python` aponta para outro ambiente.

Solução:

1. ative o `venv`;
2. confirme com:

```powershell
python -c "import sys; print(sys.executable)"
```

O caminho precisa apontar para `venv\Scripts\python.exe`.

---

### 13.3 Erro de NumPy incompatível

Sintomas:

- falhas ao importar bibliotecas nativas;
- erro envolvendo `numpy`, `faiss`, `torch` ou `sentence-transformers`.

Solução:

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

Se persistir:

```powershell
pip uninstall numpy -y
pip install numpy
```

Depois reinstale o restante se necessário.

---

### 13.4 Erro do FAISS ao salvar índice

Possíveis causas:

- caminho ruim;
- OneDrive;
- permissão;
- arquivo bloqueado;
- pasta inexistente.

Soluções:

- mova o projeto para `C:\ProjetoIC\rag_chatbot_project_v2`;
- confirme se `data/vector_store/` existe;
- feche programas que possam estar segurando o arquivo;
- evite OneDrive.

---

### 13.5 Erro por caminho com acento

Sintoma:

- comportamento estranho em bibliotecas;
- falha de indexação;
- arquivo não encontrado mesmo existindo.

Solução:

- mova o projeto para caminho simples;
- evite pastas com nomes como `Iniciação Científica`.

---

### 13.6 Erro por OneDrive

Sintoma:

- lentidão;
- arquivos reescritos;
- bloqueio durante indexação;
- erro de acesso ao `faiss.index`.

Solução:

- mova o projeto para fora do OneDrive;
- use um caminho local simples como `C:\ProjetoIC\rag_chatbot_project_v2`.

---

### 13.7 Erro de `faiss.index` não encontrado

Significado:

- a indexação ainda não foi feita;
- ou a pasta `data/vector_store/` está vazia;
- ou o projeto está apontando para outro caminho.

Solução:

```powershell
python .\index_pdfs.py
```

Depois confirme se o arquivo existe em:

```text
data/vector_store/faiss.index
```

---

### 13.8 Erro de índice vazio

Sintoma:

- `faiss.index` existe, mas o retrieval não encontra nada;
- `index_metadata.json` está vazio ou quase vazio.

Possíveis causas:

- PDFs sem texto extraível;
- falha de chunking;
- falha de embeddings;
- indexação interrompida.

Solução:

- verifique os arquivos em `data/processed/`;
- confira se `chunks.json` contém chunks reais;
- rode `debug_rag.py`.

---

### 13.9 Erro de PDF sem texto extraível

Sintoma:

- PDF está presente, mas quase nada é recuperado;
- `cleaned_text.json` sai vazio ou muito pobre.

Causa:

- o PDF pode ser escaneado como imagem;
- extração textual direta não encontra texto suficiente.

Solução:

- teste outro PDF com texto selecionável;
- considere usar OCR em uma etapa futura.

---

### 13.10 Erro de “Sem contexto recuperado”

Esse é um dos problemas mais importantes em projetos RAG.

Possíveis causas:

- extração de texto ruim;
- chunking ruim;
- embeddings inadequados;
- threshold alto demais;
- índice desatualizado;
- índice gerado com modelo diferente do configurado;
- perguntas em idioma diferente do corpus;
- retrieval filtrando todos os resultados.

Solução prática:

1. confirme que `faiss.index` existe;
2. confirme que `index_metadata.json` não está vazio;
3. confirme o `EMBEDDING_MODEL` no `.env`;
4. reindexe após mudar o modelo;
5. reduza thresholds se necessário;
6. ative debug:

```env
RAG_DEBUG=true
```

7. rode:

```powershell
python .\debug_rag.py --query laser
```

---

### 13.11 Erro de API da DeepSeek

Sintomas:

- a recuperação funciona, mas a geração falha;
- erro HTTP;
- autenticação inválida;
- timeout.

Verifique:

- `DEEPSEEK_API_KEY`;
- conexão com internet;
- modelo configurado;
- validade da chave.

Importante:

- esse tipo de erro afeta a geração;
- não explica sozinho ausência de contexto recuperado.

---

### 13.12 Aviso do Hugging Face sem login

Algumas mensagens do `sentence-transformers` e da infraestrutura da Hugging Face podem aparecer no terminal.

Nem sempre elas significam erro.

Se o modelo for baixado com sucesso e o projeto seguir normalmente, o aviso pode ser ignorado.

Se o carregamento do modelo falhar, então você precisa:

- garantir internet na primeira execução;
- ou garantir que o modelo já esteja em cache local.

---

### 13.13 Avisos de `embeddings.position_ids` ou `UNEXPECTED`

Esse tipo de aviso costuma aparecer em bibliotecas baseadas em Transformers durante o carregamento de pesos.

Na maioria dos casos:

- se o modelo carrega;
- se os embeddings são gerados;
- se não ocorre exceção final;

então o aviso pode ser apenas informativo.

Exige correção apenas se:

- o processo abortar;
- o modelo não carregar;
- a indexação falhar;
- a consulta falhar.

---

## 14. Checklist Final

Antes de considerar o projeto pronto para uso, confirme:

- o projeto está em um caminho simples, como `C:\ProjetoIC\rag_chatbot_project_v2`
- o projeto não está no OneDrive
- o caminho não tem acentos nem nomes longos
- o `venv` está criado
- o `venv` está ativado
- as dependências foram instaladas com `pip install -r requirements.txt`
- o Python ativo é o do `venv`
- o arquivo `.env` existe
- `DEEPSEEK_API_KEY` está preenchida
- `EMBEDDING_MODEL` está configurado corretamente
- os PDFs estão em `data/raw_pdfs/`
- a indexação foi executada
- o arquivo `data/vector_store/faiss.index` foi criado
- o arquivo `data/vector_store/index_metadata.json` foi criado
- o arquivo `data/vector_store/index_manifest.json` foi criado
- a pasta `data/processed/` contém saídas por documento
- `python main.py` inicia sem erro
- `streamlit run app.py` abre a interface local

Observação:

- este projeto usa `index_metadata.json`, não `metadata.pkl`.

---

## 15. Comandos Prontos

Considerando o projeto em:

```text
C:\ProjetoIC\rag_chatbot_project_v2
```

### PowerShell

```powershell
cd C:\ProjetoIC\rag_chatbot_project_v2
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python .\index_pdfs.py
python .\main.py
```

### Para rodar a interface web

```powershell
cd C:\ProjetoIC\rag_chatbot_project_v2
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
streamlit run .\app.py
```

### Para depurar o retrieval

```powershell
cd C:\ProjetoIC\rag_chatbot_project_v2
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
python .\debug_rag.py --query laser
python .\debug_rag.py --query "dor lombar"
```

---

## 16. Observação Importante Sobre o Comportamento do Chatbot

Se o chatbot sempre responde algo como:

```text
Não encontrei evidência suficiente...
```

ou:

```text
Sem contexto recuperado
```

isso normalmente indica problema em alguma parte do pipeline RAG, como:

- extração de texto;
- chunking;
- indexação;
- retrieval;
- threshold;
- modelo de embeddings;
- caminho do índice;
- incompatibilidade entre índice e modelo configurado.

Na maioria dos casos, isso não significa falha da API da DeepSeek.

Esse tipo de sintoma geralmente aponta para falha na recuperação do contexto, e não para falha de geração.

Em outras palavras:

- se não há contexto recuperado, a DeepSeek não tem base para responder;
- o problema principal costuma estar antes da etapa de geração.

---

## Árvore de Diretórios do Projeto

```text
C:\ProjetoIC\rag_chatbot_project_v2
├── .env
├── .env.example
├── app.py
├── main.py
├── index_pdfs.py
├── debug_rag.py
├── run_reports.py
├── requirements.txt
├── README.md
├── technical_report_rag.md
├── src
│   ├── chatbot.py
│   ├── chunker.py
│   ├── config.py
│   ├── embeddings.py
│   ├── evaluation.py
│   ├── history_manager.py
│   ├── llm_client.py
│   ├── pdf_loader.py
│   ├── prompt_builder.py
│   ├── prompt_profiles.py
│   ├── report_generator.py
│   ├── reranker.py
│   ├── retriever.py
│   ├── text_cleaner.py
│   ├── ui_helpers.py
│   ├── utils.py
│   └── vector_store.py
├── data
│   ├── raw_pdfs
│   ├── processed
│   └── vector_store
├── logs
│   ├── conversations
│   ├── evaluations
│   └── reports
├── tests
├── venv
└── __pycache__
```

---

## Resumo Rápido de Execução

1. Coloque o projeto em `C:\ProjetoIC\rag_chatbot_project_v2`.
2. Abra o PowerShell.
3. Entre na pasta do projeto.
4. Crie e ative o `venv`.
5. Instale `requirements.txt`.
6. Copie `.env.example` para `.env`.
7. Preencha a chave da DeepSeek.
8. Coloque seus PDFs em `data/raw_pdfs/`.
9. Rode `python index_pdfs.py`.
10. Rode `python main.py` ou `streamlit run app.py`.

---

## Sinais de Que Tudo Está Funcionando

Você pode considerar que o projeto está funcionando corretamente quando:

- o `venv` ativa sem erro;
- `pip install -r requirements.txt` termina corretamente;
- `python -c "import sys; print(sys.executable)"` aponta para o `venv`;
- o `.env` está lido sem erro;
- os PDFs estão em `data/raw_pdfs/`;
- `python index_pdfs.py` roda e gera:
  - `data/processed/...`
  - `data/vector_store/faiss.index`
  - `data/vector_store/index_metadata.json`
  - `data/vector_store/index_manifest.json`
- `python main.py` inicia sem quebrar;
- `streamlit run app.py` abre em `http://localhost:8501`;
- perguntas sobre os PDFs retornam trechos recuperados;
- perguntas fora da base retornam falta de evidência de forma controlada.

Se esses sinais aparecerem, o projeto está no caminho certo de execução.
