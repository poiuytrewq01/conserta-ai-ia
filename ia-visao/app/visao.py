"""Visão computacional: classificação zero-shot com CLIP (Hugging Face).

Zero-shot = o modelo nunca foi treinado nas nossas fotos. Ele compara o
embedding da imagem com o embedding de frases ("a photo of a pothole...")
e escolhe a frase mais parecida. Por isso não precisamos de dataset de treino.
"""
from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

from . import config
from .categorias import CATEGORIAS, ROTULOS_CLIP


class ImagemInvalida(ValueError):
    pass


def abrir_imagem(dados: bytes) -> Image.Image:
    """Valida tamanho e formato e devolve a imagem em RGB."""
    limite = config.VISAO_TAMANHO_MAX_MB * 1024 * 1024
    if len(dados) > limite:
        raise ImagemInvalida(f"Imagem maior que {config.VISAO_TAMANHO_MAX_MB:g} MB")
    try:
        img = Image.open(io.BytesIO(dados))
        img.load()
    except (UnidentifiedImageError, OSError) as e:
        raise ImagemInvalida("Arquivo não é uma imagem válida") from e
    return img.convert("RGB")


class ClassificadorClip:
    """Carrega o CLIP uma vez e reaproveita em todas as requisições."""

    def __init__(self, nome_modelo: str = config.VISAO_MODELO):
        # Import aqui dentro: os testes rodam sem precisar instalar torch.
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self.torch = torch
        self.nome_modelo = nome_modelo
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.modelo = CLIPModel.from_pretrained(nome_modelo).to(self.device).eval()
        self.processador = CLIPProcessor.from_pretrained(nome_modelo)
        self.categorias = list(CATEGORIAS)
        self._emb_texto = self._embeddings_das_categorias()

    def _embeddings_das_categorias(self):
        """Um vetor por categoria = média normalizada dos embeddings dos rótulos."""
        torch = self.torch
        vetores = []
        with torch.no_grad():
            for cat in self.categorias:
                ent = self.processador(text=ROTULOS_CLIP[cat], return_tensors="pt", padding=True).to(self.device)
                emb = self.modelo.get_text_features(**ent)
                emb = emb / emb.norm(dim=-1, keepdim=True)
                media = emb.mean(dim=0)
                vetores.append(media / media.norm())
        return torch.stack(vetores)

    def embedding_imagem(self, img: Image.Image):
        """Vetor normalizado da imagem (usado também no linear probe da avaliação)."""
        torch = self.torch
        with torch.no_grad():
            ent = self.processador(images=img, return_tensors="pt").to(self.device)
            emb = self.modelo.get_image_features(**ent)
            return (emb / emb.norm(dim=-1, keepdim=True))[0]

    def classificar(self, img: Image.Image) -> dict:
        return self.classificar_embedding(self.embedding_imagem(img))

    def classificar_embedding(self, emb) -> dict:
        torch = self.torch
        escala = self.modelo.logit_scale.exp()  # ~100, aprendido no treino do CLIP
        logits = escala * (self._emb_texto @ emb)
        probs = torch.softmax(logits, dim=0).cpu().tolist()
        scores = {c: round(p, 4) for c, p in zip(self.categorias, probs)}
        categoria = max(scores, key=scores.get)
        confianca = scores[categoria]
        return {
            "categoria": categoria,
            "confianca": confianca,
            "confiavel": confianca >= config.VISAO_LIMIAR_CONFIANCA,
            "scores": scores,
            "modelo": self.nome_modelo,
        }
