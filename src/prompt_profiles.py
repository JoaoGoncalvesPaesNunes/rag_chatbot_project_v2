from __future__ import annotations

PROMPT_PROFILES = {
    'tecnico_cientifico': {
        'label': 'Técnico-científico',
        'style_instruction': 'Use linguagem técnico-científica, precisa, densa e orientada à análise de evidências.',
    },
    'academico_formal': {
        'label': 'Acadêmico formal',
        'style_instruction': 'Use linguagem acadêmica formal, clara e organizada, adequada para iniciação científica.',
    },
    'profissional_objetivo': {
        'label': 'Profissional objetivo',
        'style_instruction': 'Use linguagem objetiva, profissional e direta, sem perder a rastreabilidade das evidências.',
    },
    'didatico_intermediario': {
        'label': 'Didático intermediário',
        'style_instruction': 'Explique de forma didática, mas mantendo rigor técnico e referências explícitas.',
    },
    'simples_acessivel': {
        'label': 'Simples/acessível',
        'style_instruction': 'Use linguagem simples e acessível, mas não omita as limitações e fontes.',
    },
}
