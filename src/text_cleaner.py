import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    # Junta palavras quebradas no fim da linha: "informa-\nção" -> "informação"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Converte quebras múltiplas em uma só
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\r", "\n", text)

    # Remove caracteres de controle, preservando quebra de linha e tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Remove espaços repetidos
    text = re.sub(r"[ \t]+", " ", text)

    # Remove muitas linhas vazias seguidas
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()