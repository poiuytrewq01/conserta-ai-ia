"""Uso responsável / LGPD: o LLM nunca recebe dado pessoal.

O LLM recebe só a descrição e a categoria. Mesmo assim o cidadão pode
digitar coisas como telefone ou email na descrição, então mascaramos antes
de enviar para o provedor externo.
"""
import re

_PADROES = [
    # email
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    # CPF (com ou sem pontuação)
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]"),
    # coordenadas "-23.5505, -46.6333"
    (re.compile(r"-?\d{1,3}\.\d{3,}\s*,\s*-?\d{1,3}\.\d{3,}"), "[COORDENADA]"),
    # telefone BR: (11) 91234-5678, 11912345678, 1234-5678
    (re.compile(r"(?<!\d)(\(?\d{2}\)?\s?)?9?\d{4}-?\d{4}(?!\d)"), "[TELEFONE]"),
    # CEP
    (re.compile(r"\b\d{5}-\d{3}\b"), "[CEP]"),
]

TAMANHO_MAX_DESCRICAO = 1000


def mascarar_dados_pessoais(texto: str) -> str:
    texto = (texto or "").strip()[:TAMANHO_MAX_DESCRICAO]
    for padrao, troca in _PADROES:
        texto = padrao.sub(troca, texto)
    return texto
