"""Gera docs/arquitetura.png (o mesmo desenho do Mermaid do README)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

LARANJA, CINZA, AZUL, VERDE = "#F28C28", "#5B6770", "#2F6DB5", "#2E8B57"
fig, ax = plt.subplots(figsize=(13, 6.6))
ax.set_xlim(0, 13); ax.set_ylim(0, 6.6); ax.axis("off")

def caixa(x, y, w, h, titulo, sub, cor):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12", fc="white", ec=cor, lw=2))
    ax.text(x + w / 2, y + h - 0.28, titulo, ha="center", va="top", fontsize=10.5, weight="bold", color=cor)
    ax.text(x + w / 2, y + h / 2 - 0.18, sub, ha="center", va="center", fontsize=8.3, color="#333")

def seta(a, b, txt="", cor=CINZA, dy=0.12, estilo="-|>"):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle=estilo, mutation_scale=14, color=cor, lw=1.6))
    if txt:
        ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + dy, txt, ha="center", fontsize=7.8, color=cor,
                bbox=dict(fc="white", ec="none", pad=0.6))

caixa(0.2, 2.6, 2.0, 1.4, "App (Expo)", "cidadão: foto +\ndescrição", CINZA)
caixa(3.1, 2.6, 2.2, 1.4, "API Java", "Spring Boot\nsalva ABERTA", AZUL)
caixa(3.1, 0.3, 2.2, 1.3, "Oracle", "ocorrência +\nresumo_ia", AZUL)
caixa(6.1, 2.6, 2.0, 1.4, "RabbitMQ", "ocorrencia.criada", CINZA)
caixa(8.9, 2.6, 2.1, 1.4, "Consumer IA", "(API Java)\nTriagemIAService", AZUL)
caixa(10.9, 4.7, 2.0, 1.6, "ia-visao", "Python + FastAPI\nCLIP zero-shot", LARANJA)
caixa(10.9, 0.3, 2.0, 1.6, "LLM (Gemini)", "Spring AI\nsaída JSON", VERDE)
caixa(6.1, 4.9, 2.6, 1.3, "Firebase Storage", "foto (URL)", CINZA)

seta((2.2, 3.3), (3.1, 3.3), "1. POST /ocorrencias")
seta((5.3, 3.3), (6.1, 3.3), "2. publica")
seta((4.2, 2.6), (4.2, 1.6), "salva", AZUL, 0)
seta((8.1, 3.3), (8.9, 3.3), "3. consome")
seta((10.4, 4.0), (11.3, 4.7), "4. foto_url", LARANJA)
seta((11.6, 4.7), (11.0, 4.0), "{categoria,\nconfiança}", LARANJA, -0.35)
seta((10.4, 2.6), (11.3, 1.9), "5. descrição +\ncategorias", VERDE, 0.05)
seta((11.7, 1.9), (11.0, 2.6), "", VERDE)
seta((8.9, 2.75), (5.3, 1.0), "6. grava prioridade, resumo, categoria IA", AZUL, 0.25)
seta((1.2, 4.0), (6.1, 5.5), "foto", CINZA)
seta((8.7, 5.5), (10.9, 5.5), "baixa a foto", LARANJA)
ax.text(8.3, 0.55, "Se a confiança da foto < 0,5 ou o LLM falhar:\ncategoria do cidadão + prioridade 3 (o fluxo nunca trava)",
        ha="center", fontsize=8.2, style="italic", color="#8B0000")
ax.text(0.2, 6.3, "Conserta Aí · fluxo da IA", fontsize=13, weight="bold", color=LARANJA)
fig.tight_layout()
fig.savefig("docs/arquitetura.png", dpi=150)
