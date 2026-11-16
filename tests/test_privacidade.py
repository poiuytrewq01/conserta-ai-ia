from app.privacidade import mascarar_dados_pessoais as m


def test_mascara_email_telefone_cpf():
    t = m("Me liga (11) 91234-5678 ou joao.silva@gmail.com, cpf 123.456.789-09")
    assert "91234" not in t and "gmail" not in t and "789" not in t
    assert "[TELEFONE]" in t and "[EMAIL]" in t and "[CPF]" in t


def test_mascara_coordenada_e_cep():
    t = m("fica em -23.6812, -46.6995 cep 04776-000")
    assert "[COORDENADA]" in t and "[CEP]" in t


def test_nao_estraga_texto_normal():
    t = "Buraco de uns 50 cm na Rua A, perto do número 120"
    assert m(t) == t


def test_corta_texto_gigante():
    assert len(m("a" * 5000)) == 1000
