from __future__ import annotations

import json

import streamlit as st

from index_pdfs import index_pdfs
from src.chatbot import AcademicRAGChatbot
from src.comparator_pipeline import ComparatorPipeline
from src.config import Config
from src.database import ResearchDatabase
from src.utils import read_json


def _load_knowledge_base() -> list[dict]:
    documents: list[dict] = []
    for metadata_path in sorted(Config.PROCESSED_DIR.glob('*/metadata.json')):
        payload = read_json(metadata_path, default={})
        if isinstance(payload, dict):
            documents.append(payload)
    return documents


def _load_json_column(value: str | None):
    if not value:
        return None
    try:
        return json.loads(value)
    except Exception:
        return value


def _percent_label(value: float | None) -> str:
    if value is None:
        return '--'
    return f'{value:.2f}%'


def _interpret_bertscore(f1_percent: float | None) -> str:
    if f1_percent is None:
        return 'Nao foi possivel interpretar o resultado porque o BERTScore nao foi calculado.'
    if f1_percent >= 85:
        return 'Alta aderencia semantica entre a resposta do TXT e os textos cientificos usados como referencia.'
    if f1_percent >= 70:
        return 'Boa aderencia semantica. A resposta parece bem alinhada aos PDFs enviados.'
    if f1_percent >= 55:
        return 'Aderencia intermediaria. Vale conferir os trechos de referencia para entender o que ficou de fora.'
    return 'Aderencia baixa. A resposta do TXT provavelmente cobre pouco do conteudo recuperado dos PDFs.'


@st.cache_resource(show_spinner=False)
def _get_database() -> ResearchDatabase:
    return ResearchDatabase(Config.SQLITE_DB_PATH)


@st.cache_resource(show_spinner=False)
def _get_chatbot() -> AcademicRAGChatbot:
    return AcademicRAGChatbot()


@st.cache_resource(show_spinner=False)
def _get_comparator_pipeline() -> ComparatorPipeline:
    return ComparatorPipeline()


def _apply_custom_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #f5efe5;
            --paper: #fffdfa;
            --paper-strong: #ffffff;
            --ink: #18242b;
            --muted: #54636d;
            --accent: #0f766e;
            --accent-strong: #0b5e58;
            --accent-2: #b85c24;
            --line: #d6cab8;
            --sidebar: #1f2a30;
            --sidebar-card: #28343b;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(15,118,110,0.09), transparent 32%),
                radial-gradient(circle at top right, rgba(184,92,36,0.10), transparent 28%),
                linear-gradient(180deg, #f8f4ec 0%, #f3ece1 100%);
            color: var(--ink);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
            background: var(--sidebar);
        }

        [data-testid="stSidebar"] * {
            color: #f5f7f8;
        }

        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: #f5f7f8;
        }

        [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {
            background: var(--sidebar-card);
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.08);
        }

        [data-testid="stSidebar"] .stButton > button {
            background: linear-gradient(135deg, #f8fafb, #edf3f4) !important;
            color: #173038 !important;
            border: 1px solid rgba(255,255,255,0.22) !important;
            box-shadow: 0 10px 22px rgba(0, 0, 0, 0.18);
        }

        [data-testid="stSidebar"] .stButton > button p,
        [data-testid="stSidebar"] .stButton > button span,
        [data-testid="stSidebar"] .stButton > button div {
            color: #173038 !important;
        }

        [data-testid="stSidebar"] .stCaption {
            color: #c5d1d6 !important;
        }

        .hero {
            background: linear-gradient(135deg, rgba(15,118,110,0.95), rgba(25,92,116,0.95));
            border: 1px solid rgba(255,255,255,0.16);
            border-radius: 24px;
            padding: 1.6rem 1.8rem;
            color: #f7fbfb;
            box-shadow: 0 18px 45px rgba(15, 118, 110, 0.16);
            margin-bottom: 1.2rem;
        }

        .hero h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.1;
            color: #f7fbfb !important;
        }

        .hero p {
            margin: 0.65rem 0 0 0;
            color: rgba(247,251,251,0.92) !important;
            max-width: 760px;
        }

        .hero-badges {
            margin-top: 1rem;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .badge {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.14);
            border: 1px solid rgba(255,255,255,0.18);
            color: #f7fbfb !important;
            font-size: 0.85rem;
        }

        .panel-card {
            background: rgba(255,253,248,0.98);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 24px rgba(31, 42, 48, 0.05);
            margin-bottom: 1rem;
        }

        .panel-card,
        .panel-card *,
        .source-card,
        .source-card *,
        .comparison-card,
        .comparison-card *,
        .comparison-metric,
        .comparison-metric *,
        .winner-banner,
        .winner-banner * {
            color: var(--ink) !important;
        }

        .muted,
        .muted *,
        .panel-card .stCaption,
        .source-card .stCaption,
        .comparison-card .stCaption {
            color: var(--muted) !important;
        }

        .source-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,242,235,0.96));
            border: 1px solid var(--line);
            border-left: 6px solid var(--accent);
            border-radius: 18px;
            padding: 1rem 1rem 0.4rem 1rem;
            margin-bottom: 0.8rem;
        }

        .comparison-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(247,243,236,0.96));
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 24px rgba(31, 42, 48, 0.05);
            margin-bottom: 1rem;
        }

        .comparison-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 0.9rem;
            width: 100%;
        }

        .comparison-metric {
            background: rgba(255,255,255,0.92);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 0.9rem 0.95rem;
            min-width: 0;
            overflow: hidden;
        }

        .comparison-metric-label {
            font-size: 0.92rem;
            color: var(--muted);
            font-weight: 700;
            margin-bottom: 0.45rem;
        }

        .comparison-metric-value {
            font-size: clamp(1.6rem, 2.3vw, 2.25rem);
            line-height: 1;
            font-weight: 800;
            color: var(--ink);
            letter-spacing: -0.04em;
            white-space: nowrap;
        }

        .winner-banner {
            background: linear-gradient(135deg, rgba(15,118,110,0.12), rgba(184,92,36,0.10));
            border: 1px solid rgba(15,118,110,0.22);
            border-radius: 18px;
            padding: 1rem 1.2rem;
            margin-bottom: 1rem;
            font-weight: 700;
            color: var(--ink);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.55rem;
            margin-bottom: 1rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255,255,255,0.56);
            border: 1px solid var(--line);
            border-radius: 999px;
            color: var(--muted) !important;
            padding: 0.45rem 1rem;
            font-weight: 700;
        }

        .stTabs [aria-selected="true"] {
            background: var(--paper-strong) !important;
            color: var(--accent-strong) !important;
            border-color: rgba(15,118,110,0.28) !important;
            box-shadow: 0 8px 20px rgba(15, 118, 110, 0.10);
        }

        .stTabs [data-baseweb="tab-highlight"] {
            background: var(--accent-2) !important;
            height: 3px !important;
        }

        [data-testid="stMetric"] {
            background: rgba(255,255,255,0.84);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            box-shadow: 0 8px 20px rgba(31, 42, 48, 0.04);
        }

        [data-testid="stMetricLabel"] {
            color: var(--muted) !important;
            font-weight: 700;
        }

        [data-testid="stMetricValue"] {
            color: var(--ink) !important;
        }

        [data-testid="stTextArea"] label,
        [data-testid="stTextInput"] label,
        [data-testid="stFileUploader"] label,
        .stNumberInput label,
        .stSlider label,
        .stRadio label,
        .stSelectbox label {
            color: var(--ink) !important;
            font-weight: 700 !important;
        }

        .stTextArea textarea,
        .stTextInput input,
        .stNumberInput input {
            background: rgba(255,255,255,0.94) !important;
            color: var(--ink) !important;
            border: 1px solid var(--line) !important;
            border-radius: 16px !important;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: rgba(255,255,255,0.7);
            border: 1px dashed rgba(15,118,110,0.35);
        }

        [data-testid="stFileUploaderDropzone"],
        [data-testid="stFileUploaderDropzone"] *,
        [data-testid="stFileUploader"] small,
        [data-testid="stFileUploader"] span,
        [data-testid="stFileUploader"] p {
            color: var(--ink) !important;
        }

        .stButton > button,
        .stForm button[kind="primary"] {
            border-radius: 14px !important;
            border: 1px solid rgba(15,118,110,0.28) !important;
            background: var(--paper-strong) !important;
            color: var(--ink) !important;
            font-weight: 700 !important;
        }

        .stForm button[kind="primary"] {
            background: linear-gradient(135deg, var(--accent), var(--accent-strong)) !important;
            color: #f7fbfb !important;
            border-color: transparent !important;
        }

        .stButton > button *,
        .stForm button[kind="primary"] * {
            color: inherit !important;
        }

        [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"],
        [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] *,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] li,
        [data-testid="stAppViewContainer"] span,
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] h4 {
            color: var(--ink);
        }

        [data-testid="stAppViewContainer"] .stCaption,
        [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"],
        [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] * {
            color: var(--muted) !important;
        }

        [data-baseweb="select"] *,
        [data-baseweb="popover"] *,
        [data-baseweb="menu"] *,
        [data-testid="stDataFrame"] *,
        [data-testid="stTable"] * {
            color: var(--ink);
        }

        [data-baseweb="input"] input,
        [data-baseweb="textarea"] textarea,
        [data-testid="stTextArea"] textarea,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input {
            color: var(--ink) !important;
            -webkit-text-fill-color: var(--ink) !important;
        }

        [data-testid="stCodeBlock"] pre,
        [data-testid="stCodeBlock"] code,
        .stCodeBlock pre,
        .stCodeBlock code {
            color: #f8fafc !important;
            background: #1f2a30 !important;
        }

        .stMarkdown,
        .stCaption,
        p,
        li,
        h1,
        h2,
        h3 {
            color: var(--ink);
        }

        [data-testid="stSidebar"],
        [data-testid="stSidebar"] *,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: #f5f7f8 !important;
        }

        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stButton > button *,
        [data-testid="stSidebar"] [data-baseweb="input"] input,
        [data-testid="stSidebar"] [data-baseweb="select"] * {
            color: #173038 !important;
            -webkit-text-fill-color: #173038 !important;
        }

        @media (max-width: 1200px) {
            .comparison-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_hero(knowledge_base_count: int) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <h1>Chatbot Academico RAG</h1>
            <p>
                Consulta local de artigos cientificos com recuperacao por embeddings, resposta guiada pelo contexto,
                BERTScore automatico, comparador PDF + TXT e persistencia em SQLite.
            </p>
            <div class="hero-badges">
                <span class="badge">PDFs indexados: {knowledge_base_count}</span>
                <span class="badge">Banco local persistente</span>
                <span class="badge">Comparador isolado da base principal</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_kb_sidebar(knowledge_base: list[dict]) -> None:
    with st.sidebar:
        st.header('Base de conhecimento')
        st.write(f'PDFs indexados: {len(knowledge_base)}')

        if st.button('Reindexar PDFs', use_container_width=True):
            with st.spinner('Reindexando PDFs locais...'):
                index_pdfs()
            _get_chatbot.clear()
            st.success('Indexacao concluida. A base foi atualizada.')

        if st.button('Limpar sessao do chat', use_container_width=True):
            st.session_state.session_history = []
            st.rerun()

        if knowledge_base:
            for item in knowledge_base:
                scientific_metadata = item.get('scientific_metadata', {})
                with st.container(border=True):
                    st.markdown(f"**{scientific_metadata.get('title') or item.get('pdf_name')}**")
                    st.caption(scientific_metadata.get('doi') or 'DOI nao identificado')
                    st.caption(
                        f"Chunks: {item.get('chunk_count', 0)} | Paginas: {item.get('page_count', 0)}"
                    )
        else:
            st.warning('Nenhum PDF indexado. Coloque arquivos em data/raw_pdfs e rode a indexacao.')


def _render_chat_summary(knowledge_base: list[dict], database: ResearchDatabase) -> None:
    interactions = database.list_interactions(limit=200)
    comparator_runs = database.list_pdf_txt_bertscore_evaluations(limit=200)
    insufficient_count = sum(1 for item in interactions if item.get('insufficient_evidence'))

    col_1, col_2, col_3, col_4 = st.columns(4)
    col_1.metric('PDFs indexados', len(knowledge_base))
    col_2.metric('Interacoes salvas', len(interactions))
    col_3.metric('Comparacoes PDF x TXT', len(comparator_runs))
    col_4.metric('Perguntas sem resposta nos PDFs', insufficient_count)


def _render_result(latest: dict) -> None:
    st.markdown('<div class="section-title">Resposta</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.write(latest['answer'])
    st.markdown('</div>', unsafe_allow_html=True)

    metric_a, metric_b, metric_c, metric_d = st.columns(4)
    metric_a.metric('BERT Precision', _percent_label(latest['bertscore'].get('precision_percent', 0.0)))
    metric_b.metric('BERT Recall', _percent_label(latest['bertscore'].get('recall_percent', 0.0)))
    metric_c.metric('BERT F1', _percent_label(latest['bertscore'].get('f1_percent', 0.0)))
    metric_d.metric('ID da interacao', latest.get('interaction_id'))

    if latest.get('errors'):
        st.error(' | '.join(latest['errors']))

    result_tab, sources_tab, debug_tab = st.tabs(
        ['Leitura da resposta', 'Trechos dos PDFs usados na resposta', 'Detalhes tecnicos']
    )

    with result_tab:
        info_left, info_right = st.columns([2, 1])
        with info_left:
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown('**Resumo da avaliacao**')
            st.write(latest['bertscore'].get('note'))
            st.write(f"Status: `{latest['bertscore'].get('status')}`")
            st.write(f"ID da avaliacao no banco: `{latest.get('evaluation_id')}`")
            st.markdown('</div>', unsafe_allow_html=True)
        with info_right:
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            st.markdown('**Registro**')
            st.write(f"Modelo LLM: `{latest.get('llm_model')}`")
            st.write(f"Chunks usados: `{len(latest.get('retrieved_chunks', []))}`")
            st.markdown('</div>', unsafe_allow_html=True)

    with sources_tab:
        st.caption('A resposta acima foi montada com base nestes trechos recuperados dos PDFs locais.')
        chunks = latest.get('retrieved_chunks', [])
        if not chunks:
            st.info('Nenhum trecho de referencia disponivel.')
        else:
            for chunk in chunks:
                st.markdown('<div class="source-card">', unsafe_allow_html=True)
                st.markdown(f"**{chunk.get('display_reference') or chunk.get('title') or chunk.get('pdf_name')}**")
                st.markdown(
                    (
                        f"<div class='muted'>DOI: {chunk.get('doi') or 'nao identificado'} | "
                        f"Paginas: {chunk.get('page_start')}-{chunk.get('page_end')} | "
                        f"Chunk: {chunk.get('chunk_id')}</div>"
                    ),
                    unsafe_allow_html=True,
                )
                with st.expander(f"Ver texto do chunk {chunk.get('chunk_id')}"):
                    st.write(chunk.get('text', ''))
                st.markdown('</div>', unsafe_allow_html=True)

    with debug_tab:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('**Log bruto do resultado**')
        st.code(json.dumps(latest, ensure_ascii=False, indent=2), language='json')
        st.markdown('</div>', unsafe_allow_html=True)


def _render_pdf_sources(chunks: list[dict]) -> None:
    if not chunks:
        st.info('Nenhum trecho de referencia foi registrado nesta avaliacao.')
        return

    for chunk in chunks:
        st.markdown('<div class="source-card">', unsafe_allow_html=True)
        st.markdown(f"**{chunk.get('display_reference') or chunk.get('title') or chunk.get('pdf_name')}**")
        st.markdown(
            (
                f"<div class='muted'>DOI: {chunk.get('doi') or 'nao identificado'} | "
                f"Paginas: {chunk.get('page_start') or '-'}-{chunk.get('page_end') or '-'} | "
                f"Trecho: {chunk.get('chunk_id') or 'referencia_pdf'}</div>"
            ),
            unsafe_allow_html=True,
        )
        if chunk.get('vector_score') is not None:
            st.caption(f"Score vetorial: {chunk.get('vector_score'):.4f}")
        st.write(chunk.get('text', ''))
        st.markdown('</div>', unsafe_allow_html=True)


def _render_pdf_txt_result(result: dict, saved_id: int | None) -> None:
    bertscore = result.get('bertscore', {})
    reference = result.get('reference', {})
    documents = result.get('documents', [])

    st.markdown(
        (
            "<div class='winner-banner'>"
            f"Interpretacao: {_interpret_bertscore(bertscore.get('f1_percent'))}"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    metric_a, metric_b, metric_c, metric_d = st.columns(4)
    metric_a.metric('BERT Precision', _percent_label(bertscore.get('precision_percent')))
    metric_b.metric('BERT Recall', _percent_label(bertscore.get('recall_percent')))
    metric_c.metric('BERT F1', _percent_label(bertscore.get('f1_percent')))
    metric_d.metric('ID salvo no banco', saved_id if saved_id is not None else '--')

    info_left, info_right = st.columns([2, 1], vertical_alignment='top')
    with info_left:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('**Resumo da comparacao**')
        st.write(
            'O sistema comparou o TXT usando o mesmo fluxo do chatbot principal: recuperacao vetorial, reranking, selecao de Top-K e depois BERTScore.'
        )
        st.write(f"Modo de referencia: `{result.get('reference_mode')}`")
        st.write(f"Pergunta usada na analise: `{result.get('question_or_theme') or 'nao informado'}`")
        st.write(f"Status do calculo: `{bertscore.get('status')}`")
        st.markdown('</div>', unsafe_allow_html=True)
    with info_right:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('**Arquivos usados**')
        st.write(f"PDFs enviados: `{len(documents)}`")
        st.write(f"TXT avaliado: `{result.get('txt', {}).get('file_name')}`")
        st.markdown('</div>', unsafe_allow_html=True)

    docs_tab, reference_tab, txt_tab, debug_tab = st.tabs(
        ['PDFs enviados', 'Trechos usados como referencia', 'Texto do TXT', 'Detalhes tecnicos']
    )

    with docs_tab:
        for document in documents:
            st.markdown('<div class="panel-card">', unsafe_allow_html=True)
            scientific_metadata = document.get('scientific_metadata', {})
            st.markdown(f"**{scientific_metadata.get('title') or document.get('file_name')}**")
            st.caption(scientific_metadata.get('doi') or 'DOI nao identificado')
            st.write(
                f"Paginas: `{document.get('page_count', 0)}` | Chunks: `{document.get('chunk_count', 0)}`"
            )
            if document.get('errors'):
                st.warning(' | '.join(document['errors']))
            st.markdown('</div>', unsafe_allow_html=True)

    with reference_tab:
        st.caption('Os trechos abaixo vieram somente dos PDFs enviados nesta comparacao.')
        _render_pdf_sources(reference.get('chunks', []))
        with st.expander('Ver texto de referencia completo usado no BERTScore'):
            st.write(reference.get('reference_text', ''))

    with txt_tab:
        txt_payload = result.get('txt', {})
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown(f"**Arquivo TXT:** `{txt_payload.get('file_name')}`")
        st.write(txt_payload.get('text', ''))
        st.markdown('</div>', unsafe_allow_html=True)

    with debug_tab:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('**Log bruto do comparador**')
        st.code(json.dumps(result, ensure_ascii=False, indent=2), language='json')
        st.markdown('</div>', unsafe_allow_html=True)


def _render_comparator_tab(database: ResearchDatabase, comparator_pipeline: ComparatorPipeline) -> None:
    st.subheader('Comparador BERTScore')
    st.caption(
        'Envie PDFs cientificos e um arquivo TXT com a resposta que voce quer avaliar. '
        'Essa analise usa apenas os PDFs enviados agora e segue a mesma logica de BERTScore do chatbot principal, sem sobrescrever a base principal.'
    )

    with st.form('pdf_txt_comparator_form', clear_on_submit=False):
        uploaded_pdfs = st.file_uploader(
            'PDFs de referencia',
            type=['pdf'],
            accept_multiple_files=True,
            help='Esses PDFs serao processados separadamente apenas para esta comparacao.',
        )
        uploaded_txt = st.file_uploader(
            'Arquivo TXT com a resposta a ser avaliada',
            type=['txt'],
            accept_multiple_files=False,
        )
        question_or_theme = st.text_area(
            'Pergunta usada para a mesma analise do chatbot principal',
            height=100,
            placeholder='Exemplo: Quais protocolos de fotobiomodulacao foram mais eficazes para dor lombar cronica?',
        )
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('**Fluxo usado**')
        st.write('O sistema seleciona automaticamente os trechos mais relevantes dos PDFs e depois calcula o BERTScore.')
        st.caption('Esse processo segue a mesma logica interna do chatbot principal.')
        st.markdown('</div>', unsafe_allow_html=True)

        submitted = st.form_submit_button('Calcular BERTScore', type='primary', use_container_width=True)

    if not submitted:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('**Como usar**')
        st.write('1. Envie um ou mais PDFs.')
        st.write('2. Envie um TXT com a resposta de outro chatbot ou sistema.')
        st.write('3. Informe a mesma pergunta que seria usada no chatbot principal.')
        st.write('4. Clique em calcular para repetir a mesma logica de recuperacao e avaliacao do chat.')
        st.markdown('</div>', unsafe_allow_html=True)
        return

    if not (question_or_theme or '').strip():
        st.warning('Informe a pergunta para usar exatamente o mesmo fluxo do chatbot principal.')
        return

    try:
        with st.spinner('Processando PDFs enviados e calculando o BERTScore...'):
            result = comparator_pipeline.evaluate_txt_against_pdfs(
                uploaded_pdfs=uploaded_pdfs or [],
                txt_file=uploaded_txt,
                question_or_theme=question_or_theme,
                reference_mode=ComparatorPipeline.CHATBOT_FLOW_MODE,
                top_k=Config.TOP_K,
            )
    except Exception as exc:
        st.error(f'Nao foi possivel executar a comparacao: {exc}')
        return

    saved_id = None
    try:
        saved_id = database.save_pdf_txt_bertscore_evaluation(
            {
                'question_or_theme': result.get('question_or_theme'),
                'reference_mode': result.get('reference_mode'),
                'top_k': result.get('top_k'),
                'txt_file_name': result.get('txt', {}).get('file_name'),
                'txt_encoding': result.get('txt', {}).get('encoding'),
                'uploaded_pdfs': result.get('documents', []),
                'reference_text': result.get('reference', {}).get('reference_text'),
                'reference_chunks': result.get('reference', {}).get('chunks', []),
                'candidate_text': result.get('txt', {}).get('text'),
                'bertscore': result.get('bertscore', {}),
                'status': result.get('status'),
                'logs': result.get('logs', {}),
                'error': result.get('error'),
            }
        )
    except Exception as exc:
        st.warning(f'Comparacao calculada, mas nao foi possivel salvar no banco: {exc}')

    if result.get('status') == 'not_run':
        st.warning('Nao houve contexto suficiente recuperado dos PDFs enviados para calcular o BERTScore.')
        _render_pdf_txt_result(result, saved_id)
        return

    if result.get('status') != 'ok':
        st.error(result.get('error') or result.get('bertscore', {}).get('error') or 'Falha na comparacao.')
        if result.get('reference', {}).get('reference_text'):
            with st.expander('Ver texto de referencia parcial gerado antes da falha'):
                st.write(result['reference']['reference_text'])
        return

    _render_pdf_txt_result(result, saved_id)


def _render_database_panel(database: ResearchDatabase) -> None:
    st.subheader('Banco de dados SQLite')
    st.caption(f'Arquivo: {Config.SQLITE_DB_PATH}')

    interactions = database.list_interactions(limit=500)
    evaluations = database.list_bert_evaluations(limit=500)
    pdf_txt_evaluations = database.list_pdf_txt_bertscore_evaluations(limit=500)
    legacy_comparisons = database.list_response_comparisons(limit=500)

    stats_a, stats_b, stats_c, stats_d = st.columns(4)
    stats_a.metric('Interacoes', len(interactions))
    stats_b.metric('Avaliacoes do chat', len(evaluations))
    stats_c.metric('Comparacoes PDF x TXT', len(pdf_txt_evaluations))
    stats_d.metric('Comparacoes antigas', len(legacy_comparisons))

    section_interactions, section_pdf_txt, section_legacy = st.tabs(
        ['Interacoes do chatbot', 'Comparador BERTScore', 'Comparacoes antigas']
    )

    with section_interactions:
        if interactions:
            interaction_rows = [
                {
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'question': row['question'],
                    'llm_model': row['llm_model'],
                    'insufficient_evidence': row['insufficient_evidence'],
                    'error': row['error'],
                }
                for row in interactions[:20]
            ]
            st.dataframe(interaction_rows, use_container_width=True, hide_index=True)
        else:
            st.info('Nenhuma interacao encontrada no banco ainda.')

    with section_pdf_txt:
        if pdf_txt_evaluations:
            evaluation_rows = [
                {
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'question_or_theme': row['question_or_theme'],
                    'reference_mode': row['reference_mode'],
                    'top_k': row['top_k'],
                    'txt_file_name': row['txt_file_name'],
                    'bert_f1_percent': row['bert_f1_percent'],
                    'status': row['status'],
                }
                for row in pdf_txt_evaluations[:20]
            ]
            st.dataframe(evaluation_rows, use_container_width=True, hide_index=True)
            selected_id = st.number_input(
                'Ver detalhe da comparacao PDF x TXT',
                min_value=1,
                value=int(pdf_txt_evaluations[0]['id']),
                step=1,
            )
            selected_evaluation = database.get_pdf_txt_bertscore_evaluation_by_id(int(selected_id))
            if selected_evaluation:
                st.json(
                    {
                        **selected_evaluation,
                        'uploaded_pdfs_json': _load_json_column(selected_evaluation.get('uploaded_pdfs_json')),
                        'reference_chunks_json': _load_json_column(selected_evaluation.get('reference_chunks_json')),
                        'logs_json': _load_json_column(selected_evaluation.get('logs_json')),
                    }
                )
        else:
            st.info('Nenhuma comparacao PDF x TXT salva ainda.')

    with section_legacy:
        if legacy_comparisons:
            comparison_rows = [
                {
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'base_question': row['base_question'],
                    'top_k': row['top_k'],
                    'reference_mode': row['reference_mode'],
                    'winner': row['winner'],
                }
                for row in legacy_comparisons[:20]
            ]
            st.dataframe(comparison_rows, use_container_width=True, hide_index=True)
            selected_comparison_id = st.number_input(
                'Ver detalhe da comparacao antiga',
                min_value=1,
                value=int(legacy_comparisons[0]['id']),
                step=1,
                key='legacy_comparison_id',
            )
            selected_comparison = database.get_response_comparison_by_id(int(selected_comparison_id))
            if selected_comparison:
                st.json(
                    {
                        **selected_comparison,
                        'reference_chunks_json': _load_json_column(selected_comparison.get('reference_chunks_json')),
                        'logs_json': _load_json_column(selected_comparison.get('logs_json')),
                    }
                )
        else:
            st.info('Nenhuma comparacao antiga salva no banco.')


st.set_page_config(page_title='Chatbot Academico RAG', layout='wide')
_apply_custom_theme()

if 'session_history' not in st.session_state:
    st.session_state.session_history = []

knowledge_base = _load_knowledge_base()
database = _get_database()
_render_kb_sidebar(knowledge_base)
_render_hero(len(knowledge_base))

initialization_error = None
chatbot = None
comparator_pipeline = None
try:
    chatbot = _get_chatbot()
    comparator_pipeline = _get_comparator_pipeline()
except Exception as exc:
    initialization_error = exc

tab_chat, tab_comparator, tab_database = st.tabs(['Chat', 'Comparador BERTScore', 'Banco de dados'])

with tab_chat:
    _render_chat_summary(knowledge_base, database)

    left_col, right_col = st.columns([3, 1], vertical_alignment='top')

    with left_col:
        with st.form('chat_question_form', clear_on_submit=False):
            question = st.text_area(
                'Pergunta',
                placeholder='Exemplo: O que os artigos dizem sobre laser para dor lombar cronica?',
                height=110,
            )
            submit_question = st.form_submit_button('Perguntar', type='primary', use_container_width=True)

        if submit_question:
            if initialization_error:
                st.error(f'Erro ao inicializar o chatbot: {initialization_error}')
            elif question.strip():
                with st.spinner('Consultando base local e gerando resposta...'):
                    result = chatbot.ask(question.strip())
                st.session_state.session_history.append(result)
            else:
                st.warning('Digite uma pergunta antes de enviar.')

        if st.session_state.session_history:
            latest = st.session_state.session_history[-1]
            _render_result(latest)
        else:
            st.info(
                'Envie uma pergunta para ver a resposta, os trechos dos PDFs usados na resposta e os registros do banco.'
            )

    with right_col:
        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('**Modo atual**')
        st.write('O chat responde sempre com base nos trechos recuperados dos PDFs locais.')
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel-card">', unsafe_allow_html=True)
        st.markdown('**Historico da sessao**')
        if st.session_state.session_history:
            for idx, item in enumerate(reversed(st.session_state.session_history), start=1):
                st.markdown(f"**{idx}.** {item['question']}")
        else:
            st.caption('As perguntas feitas nesta sessao aparecerao aqui.')
        st.markdown('</div>', unsafe_allow_html=True)

with tab_comparator:
    if initialization_error:
        st.error(f'Erro ao inicializar o comparador: {initialization_error}')
    else:
        _render_comparator_tab(database, comparator_pipeline)

with tab_database:
    _render_database_panel(database)
