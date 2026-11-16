"""ia-visao: serviço de IA do Conserta Aí (FastAPI).

Rotas:
  GET  /health                 -> status do modelo de visão e do LLM
  POST /visao/classificar      -> foto (upload) -> {categoria, confianca, scores}
  POST /visao/classificar-url  -> {"foto_url": ...} (é o que a API Java usa: a foto já está no Firebase)
  POST /triagem                -> descrição + categorias -> LLM -> {categoria_final, prioridade, resumo_tecnico, justificativa}
  POST /analisar               -> foto + descrição: visão + triagem em uma chamada (demo no Swagger)

Rodar:  uvicorn app.main:app --reload --port 8000   (Swagger em /docs)
"""
from __future__ import annotations

import ipaddress
import logging
import socket
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from . import config
from .categorias import CATEGORIAS
from .triagem import Triador
from .visao import ImagemInvalida, abrir_imagem

log = logging.getLogger("ia-visao")
estado: dict = {"classificador": None, "erro_visao": None, "triador": None}


def carregar_classificador():
    from .visao import ClassificadorClip

    return ClassificadorClip()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Carrega o CLIP uma vez na subida (demora ~10 s); requisições ficam rápidas depois.
    if estado["classificador"] is None:
        try:
            estado["classificador"] = carregar_classificador()
        except Exception as e:  # sobe mesmo assim; /health mostra o problema
            estado["erro_visao"] = str(e)
            log.exception("Falha ao carregar o modelo de visão")
    if estado["triador"] is None:
        estado["triador"] = Triador()
    yield


app = FastAPI(
    title="Conserta Aí - ia-visao",
    description="Visão computacional (CLIP zero-shot) + triagem generativa (LLM) para ocorrências de zeladoria.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------- modelos de entrada/saída (aparecem no Swagger) ----------
class ClassificarUrlIn(BaseModel):
    foto_url: str = Field(examples=["https://firebasestorage.googleapis.com/.../foto.jpg"])


class TriagemIn(BaseModel):
    descricao: str = Field(min_length=3, max_length=2000, examples=["Buraco enorme na frente da escola, carro quase caiu"])
    categoria_cidadao: str = Field(examples=["Buraco"])
    categoria_foto: str | None = Field(default=None, examples=["Buraco"])
    confianca_foto: float | None = Field(default=None, ge=0, le=1, examples=[0.82])


# ---------- helpers ----------
def _classificador():
    if estado["classificador"] is None:
        raise HTTPException(503, f"Modelo de visão indisponível: {estado['erro_visao']}")
    return estado["classificador"]


def _classificar_bytes(dados: bytes) -> dict:
    try:
        img = abrir_imagem(dados)
    except ImagemInvalida as e:
        raise HTTPException(422, str(e))
    return _classificador().classificar(img)


def _url_segura(url: str) -> bool:
    """Evita SSRF: só http(s) e nunca IP interno (localhost, rede privada)."""
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname:
        return False
    try:
        for info in socket.getaddrinfo(p.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
    except (socket.gaierror, ValueError):
        return False
    return True


# ---------- rotas ----------
@app.get("/health")
def health():
    visao_ok = estado["classificador"] is not None
    llm_ok = estado["triador"] is not None and estado["triador"].cliente is not None
    return {
        "status": "UP" if visao_ok and llm_ok else "DEGRADED",
        "visao": {"ok": visao_ok, "modelo": config.VISAO_MODELO, "erro": estado["erro_visao"]},
        "llm": {"ok": llm_ok, "modelo": config.LLM_MODELO},
    }


@app.post("/visao/classificar")
async def classificar(foto: UploadFile = File(...)):
    return _classificar_bytes(await foto.read())


@app.post("/visao/classificar-url")
def classificar_url(body: ClassificarUrlIn):
    if not _url_segura(body.foto_url):
        raise HTTPException(422, "URL da foto inválida")
    try:
        r = httpx.get(body.foto_url, timeout=10, follow_redirects=False)
        r.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(422, "Não foi possível baixar a foto")
    return _classificar_bytes(r.content)


@app.post("/triagem")
def triagem(body: TriagemIn):
    return estado["triador"].triar(body.descricao, body.categoria_cidadao, body.categoria_foto, body.confianca_foto)


@app.post("/analisar")
async def analisar(
    foto: UploadFile = File(...),
    descricao: str = Form(...),
    categoria_cidadao: str = Form(..., description=", ".join(CATEGORIAS)),
):
    visao = _classificar_bytes(await foto.read())
    # Foto com confiança baixa não influencia o LLM (regra do limiar 0,5)
    cat_foto = visao["categoria"] if visao["confiavel"] else None
    conf_foto = visao["confianca"] if visao["confiavel"] else None
    tri = estado["triador"].triar(descricao, categoria_cidadao, cat_foto, conf_foto)
    return {"visao": visao, "triagem": tri}
