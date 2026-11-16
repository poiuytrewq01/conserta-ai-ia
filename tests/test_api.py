import io
import json

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import main
from app.triagem import Triador
from tests.test_triagem import OK, LLMFalso


class ClassificadorFalso:
    def __init__(self, cat="Buraco", conf=0.8):
        self.cat, self.conf = cat, conf

    def classificar(self, img):
        return {"categoria": self.cat, "confianca": self.conf, "confiavel": self.conf >= 0.5, "scores": {}, "modelo": "falso"}


def _png():
    b = io.BytesIO()
    Image.new("RGB", (32, 32), "gray").save(b, "PNG")
    return b.getvalue()


@pytest.fixture
def cliente():
    main.estado.update(classificador=ClassificadorFalso(), erro_visao=None, triador=Triador(cliente=LLMFalso([OK] * 5)))
    with TestClient(main.app) as c:
        yield c


def test_health(cliente):
    assert cliente.get("/health").json()["status"] == "UP"


def test_classificar_foto(cliente):
    r = cliente.post("/visao/classificar", files={"foto": ("a.png", _png(), "image/png")})
    assert r.status_code == 200 and r.json()["categoria"] == "Buraco"


def test_arquivo_que_nao_e_imagem(cliente):
    r = cliente.post("/visao/classificar", files={"foto": ("a.txt", b"oi", "text/plain")})
    assert r.status_code == 422


def test_url_interna_bloqueada(cliente):
    r = cliente.post("/visao/classificar-url", json={"foto_url": "http://127.0.0.1/admin"})
    assert r.status_code == 422


def test_triagem(cliente):
    r = cliente.post("/triagem", json={"descricao": "buraco enorme", "categoria_cidadao": "Buraco"})
    assert r.json()["prioridade"] == 5


def test_analisar_foto_com_baixa_confianca_nao_vai_pro_llm(cliente):
    llm = LLMFalso([OK])
    main.estado.update(classificador=ClassificadorFalso("Lixo", 0.3), triador=Triador(cliente=llm))
    r = cliente.post("/analisar", files={"foto": ("a.png", _png(), "image/png")}, data={"descricao": "buraco", "categoria_cidadao": "Buraco"})
    enviado = json.loads(llm.recebido[0]["messages"][1]["content"])
    assert r.status_code == 200 and enviado["categoria_foto"] is None


def test_visao_fora_do_ar_responde_503(cliente):
    main.estado.update(classificador=None, erro_visao="sem modelo")
    r = cliente.post("/visao/classificar", files={"foto": ("a.png", _png(), "image/png")})
    assert r.status_code == 503
