"""Configuração lida de variáveis de ambiente (nunca de código).

Copie `.env.example` para `.env` e preencha. O `.env` está no .gitignore.
"""
import os

from dotenv import load_dotenv

load_dotenv()

# Visão computacional
VISAO_MODELO = os.getenv("VISAO_MODELO", "openai/clip-vit-base-patch32")
VISAO_LIMIAR_CONFIANCA = float(os.getenv("VISAO_LIMIAR_CONFIANCA", "0.5"))
VISAO_TAMANHO_MAX_MB = float(os.getenv("VISAO_TAMANHO_MAX_MB", "10"))

# IA generativa (qualquer provedor compatível com a API da OpenAI; padrão: Gemini)
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODELO = os.getenv("LLM_MODELO", "gemini-flash-latest")
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "20"))

# Regra de negócio do fallback (definida no plano do projeto)
PRIORIDADE_PADRAO = 3
