import json
from types import SimpleNamespace

from app.triagem import Triador, extrair_json


class LLMFalso:
    """Imita o cliente da OpenAI devolvendo respostas pré-definidas."""

    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.recebido = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kw):
        self.recebido.append(kw)
        r = self.respostas.pop(0)
        if isinstance(r, Exception):
            raise r
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=r))])


OK = json.dumps({"categoria_final": "buraco", "prioridade": 5, "resumo_tecnico": "Buraco grande em via movimentada.", "justificativa": "Risco de acidente."})


def test_saida_valida():
    r = Triador(cliente=LLMFalso([OK])).triar("buraco enorme", "Buraco")
    assert r["origem"] == "llm" and r["categoria_final"] == "Buraco" and r["prioridade"] == 5


def test_aceita_json_em_markdown():
    assert extrair_json("```json\n" + OK + "\n```")["prioridade"] == 5


def test_json_quebrado_tenta_de_novo():
    r = Triador(cliente=LLMFalso(["isso não é json", OK])).triar("buraco", "Buraco")
    assert r["origem"] == "llm"


def test_categoria_inventada_vai_para_fallback():
    ruim = OK.replace("buraco", "Enchente")
    r = Triador(cliente=LLMFalso([ruim, ruim])).triar("alagou", "Outros")
    assert r["origem"] == "fallback" and r["prioridade"] == 3


def test_prioridade_fora_da_escala_vai_para_fallback():
    ruim = OK.replace('"prioridade": 5', '"prioridade": 9')
    r = Triador(cliente=LLMFalso([ruim, ruim])).triar("x x x", "Lixo")
    assert r["origem"] == "fallback" and r["categoria_final"] == "Lixo"


def test_provedor_fora_do_ar_nao_trava():
    r = Triador(cliente=LLMFalso([TimeoutError("timeout")])).triar("poste apagado", "Iluminação")
    assert r["origem"] == "fallback" and r["categoria_final"] == "Iluminação" and r["prioridade"] == 3


def test_sem_chave_usa_fallback():
    t = Triador(cliente=None)
    t.cliente = None
    assert t.triar("lixo", "Lixo")["origem"] == "fallback"


def test_llm_nao_recebe_dado_pessoal():
    llm = LLMFalso([OK])
    Triador(cliente=llm).triar("buraco, me liga 11912345678 joao@x.com", "Buraco")
    enviado = llm.recebido[0]["messages"][1]["content"]
    assert "11912345678" not in enviado and "joao@x.com" not in enviado


def test_temperatura_zero():
    llm = LLMFalso([OK])
    Triador(cliente=llm).triar("buraco", "Buraco")
    assert llm.recebido[0]["temperature"] == 0
