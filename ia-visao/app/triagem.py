"""IA generativa: triagem do relato com um LLM (saída estruturada em JSON).

Usa a biblioteca `openai` apontando para qualquer provedor compatível
(padrão: Gemini, que tem camada gratuita). Trocar de provedor = trocar 3
variáveis no .env, sem mudar código. É o mesmo prompt usado pela API Java
com Spring AI (pasta prompts/).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator

from . import config
from .categorias import CATEGORIAS
from .privacidade import mascarar_dados_pessoais

_CAMINHOS_PROMPT = [
    Path(__file__).resolve().parents[2] / "prompts" / "triagem_sistema.txt",  # repositório
    Path(__file__).resolve().parents[1] / "prompts" / "triagem_sistema.txt",  # dentro do container
]
PROMPT_SISTEMA = next(p for p in _CAMINHOS_PROMPT if p.exists()).read_text(encoding="utf-8")


class SaidaLLM(BaseModel):
    """Contrato da resposta do LLM. Se não bater, cai no fallback."""

    categoria_final: str
    prioridade: int = Field(ge=1, le=5)
    resumo_tecnico: str = Field(min_length=5, max_length=600)
    justificativa: str = Field(min_length=3, max_length=400)

    @field_validator("categoria_final")
    @classmethod
    def categoria_valida(cls, v: str) -> str:
        v = v.strip()
        for c in CATEGORIAS:
            if v.lower() == c.lower():
                return c
        raise ValueError(f"categoria inválida: {v}")


def extrair_json(texto: str) -> dict:
    """Aceita a resposta mesmo se o modelo embrulhar em ```json ... ```."""
    texto = (texto or "").strip()
    m = re.search(r"\{.*\}", texto, re.DOTALL)
    if not m:
        raise ValueError("resposta sem JSON")
    return json.loads(m.group(0))


def _criar_cliente():
    from openai import OpenAI

    if not config.LLM_API_KEY:
        return None
    return OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL, timeout=config.LLM_TIMEOUT_S, max_retries=config.LLM_MAX_RETRIES)


class Triador:
    def __init__(self, cliente=None, modelo: str = config.LLM_MODELO):
        self.cliente = cliente if cliente is not None else _criar_cliente()
        self.modelo = modelo

    def _chamar_llm(self, entrada: dict) -> str:
        resp = self.cliente.chat.completions.create(
            model=self.modelo,
            temperature=0,  # mesma entrada -> mesma saída (reprodutível)
            messages=[
                {"role": "system", "content": PROMPT_SISTEMA},
                {"role": "user", "content": json.dumps(entrada, ensure_ascii=False)},
            ],
        )
        return resp.choices[0].message.content or ""

    def triar(
        self,
        descricao: str,
        categoria_cidadao: str,
        categoria_foto: str | None = None,
        confianca_foto: float | None = None,
    ) -> dict:
        inicio = time.perf_counter()
        entrada = {
            "descricao": mascarar_dados_pessoais(descricao),
            "categoria_cidadao": categoria_cidadao,
            "categoria_foto": categoria_foto,
            "confianca_foto": confianca_foto,
        }
        erro = None
        json_valido = False
        resposta_bruta = ""
        if self.cliente is None:
            erro = "LLM_API_KEY não configurada"
        else:
            # 2 tentativas: a segunda cobre JSON quebrado ocasional
            for _ in range(2):
                try:
                    resposta_bruta = self._chamar_llm(entrada)
                    saida = SaidaLLM(**extrair_json(resposta_bruta))
                    json_valido = True
                    return {
                        **saida.model_dump(),
                        "origem": "llm",
                        "modelo": self.modelo,
                        "json_valido": True,
                        "latencia_ms": round((time.perf_counter() - inicio) * 1000),
                    }
                except (ValueError, ValidationError, json.JSONDecodeError) as e:
                    erro = f"saída inválida: {e}"
                except Exception as e:  # rede, cota, timeout... o fluxo nunca trava por causa da IA
                    erro = f"falha no provedor: {type(e).__name__}: {str(e)[:200]}"
                    break
        return self._fallback(categoria_cidadao, erro, json_valido, inicio)

    def _fallback(self, categoria_cidadao: str, erro: str | None, json_valido: bool, inicio: float) -> dict:
        """Regra do plano: se o LLM falhar, vale a categoria do cidadão e prioridade 3."""
        cat = categoria_cidadao if categoria_cidadao in CATEGORIAS else "Outros"
        return {
            "categoria_final": cat,
            "prioridade": config.PRIORIDADE_PADRAO,
            "resumo_tecnico": None,
            "justificativa": "Triagem automática indisponível; usada a categoria do cidadão e prioridade padrão.",
            "origem": "fallback",
            "modelo": self.modelo,
            "json_valido": json_valido,
            "erro": erro,
            "latencia_ms": round((time.perf_counter() - inicio) * 1000),
        }
