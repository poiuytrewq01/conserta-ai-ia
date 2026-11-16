"""Avaliação da visão computacional: CLIP zero-shot x linear probe.

- Zero-shot: o CLIP como está, comparando a foto com os rótulos em texto.
- Linear probe (Machine Learning): uma regressão logística treinada em cima
  dos embeddings do CLIP, com validação cruzada de 5 dobras. Mostra quanto
  ganharíamos treinando uma camada simples com as nossas fotos.

Métricas: acurácia, F1 macro, matriz de confusão, cobertura do limiar 0,5.

Uso:  python avaliacao/avaliar_visao.py
Saída: avaliacao/resultados/visao_*.{json,csv,png,md}
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import ConfusionMatrixDisplay, accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ.parent / "ia-visao"))
from app import config  # noqa: E402
from app.visao import ClassificadorClip  # noqa: E402

DADOS = RAIZ / "dados"
RES = RAIZ / "resultados"
EXCLUIDAS = DADOS / "fotos_excluidas.txt"  # uma linha por arquivo (ex.: fotos/lixo/x.jpg) para tirar fotos ruins


def salvar_matriz(y_true, y_pred, rotulos, titulo, arquivo):
    cm = confusion_matrix(y_true, y_pred, labels=rotulos)
    fig, ax = plt.subplots(figsize=(7, 6))
    ConfusionMatrixDisplay(cm, display_labels=rotulos).plot(ax=ax, cmap="Oranges", colorbar=False, xticks_rotation=35)
    ax.set_title(titulo)
    ax.set_xlabel("Previsto")
    ax.set_ylabel("Real")
    fig.tight_layout()
    fig.savefig(RES / arquivo, dpi=130)
    plt.close(fig)


def main():
    RES.mkdir(exist_ok=True)
    excluidas = set(EXCLUIDAS.read_text(encoding="utf-8").split()) if EXCLUIDAS.exists() else set()
    with (DADOS / "manifest_fotos.csv").open(encoding="utf-8") as fh:
        itens = [l for l in csv.DictReader(fh) if l["arquivo"] not in excluidas and (DADOS / l["arquivo"]).exists()]
    print(f"{len(itens)} imagens. Carregando {config.VISAO_MODELO}...")

    clf = ClassificadorClip()
    linhas, embs = [], []
    for it in itens:
        emb = clf.embedding_imagem(Image.open(DADOS / it["arquivo"]).convert("RGB"))
        r = clf.classificar_embedding(emb)
        embs.append(emb.cpu().numpy())
        linhas.append({**it, "previsto": r["categoria"], "confianca": r["confianca"], "confiavel": r["confiavel"]})

    teste = [i for i, l in enumerate(linhas) if l["conjunto"] == "teste"]
    y = [linhas[i]["categoria"] for i in teste]
    p = [linhas[i]["previsto"] for i in teste]
    rotulos = [c for c in clf.categorias if c in set(y)]

    # ---- zero-shot ----
    zs = {
        "n_imagens": len(teste),
        "por_categoria": dict(Counter(y)),
        "acuracia": round(accuracy_score(y, p), 4),
        "f1_macro": round(f1_score(y, p, labels=rotulos, average="macro", zero_division=0), 4),
    }
    conf = [i for i in teste if linhas[i]["confiavel"]]
    zs["cobertura_limiar"] = round(len(conf) / len(teste), 4)  # % de fotos com confiança >= 0,5
    zs["acuracia_acima_limiar"] = round(accuracy_score([linhas[i]["categoria"] for i in conf], [linhas[i]["previsto"] for i in conf]), 4) if conf else None
    zs["relatorio"] = classification_report(y, p, labels=rotulos, output_dict=True, zero_division=0)
    salvar_matriz(y, p, rotulos, "CLIP zero-shot", "visao_matriz_zeroshot.png")

    # ---- linear probe (ML sobre embeddings, validação cruzada) ----
    X = np.stack([embs[i] for i in teste])
    menor = min(Counter(y).values())
    lp = None
    if menor >= 2:
        k = min(5, menor)
        pred_lp = cross_val_predict(LogisticRegression(max_iter=2000, C=10), X, y, cv=StratifiedKFold(k, shuffle=True, random_state=42))
        lp = {
            "dobras": k,
            "acuracia": round(accuracy_score(y, pred_lp), 4),
            "f1_macro": round(f1_score(y, pred_lp, labels=rotulos, average="macro", zero_division=0), 4),
        }
        salvar_matriz(y, pred_lp, rotulos, f"Linear probe ({k}-fold)", "visao_matriz_linear_probe.png")
        for i, pr in zip(teste, pred_lp):
            linhas[i]["previsto_linear_probe"] = pr

    # ---- casos de falha ----
    falhas = [{"arquivo": l["arquivo"], "esperado": l["categoria"], "previsto": l["previsto"], "confianca": l["confianca"], "confiavel": l["confiavel"]} for l in linhas if l["conjunto"] == "falha"]

    metricas = {"modelo": config.VISAO_MODELO, "limiar": config.VISAO_LIMIAR_CONFIANCA, "zero_shot": zs, "linear_probe": lp, "casos_falha": falhas}
    (RES / "visao_metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    campos = ["arquivo", "conjunto", "categoria", "previsto", "confianca", "confiavel", "previsto_linear_probe", "fonte", "licenca", "link"]
    with (RES / "visao_predicoes.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(linhas)

    # ---- resumo em markdown (vai para o README) ----
    md = [
        "## Resultados - Visão computacional",
        f"Modelo: `{config.VISAO_MODELO}` | {zs['n_imagens']} fotos de teste | por categoria: {zs['por_categoria']}",
        "",
        "| Abordagem | Acurácia | F1 macro |",
        "|---|---|---|",
        f"| CLIP zero-shot | {zs['acuracia']:.1%} | {zs['f1_macro']:.3f} |",
    ]
    if lp:
        md.append(f"| Linear probe ({lp['dobras']}-fold) | {lp['acuracia']:.1%} | {lp['f1_macro']:.3f} |")
    md += [
        "",
        f"Limiar de confiança {config.VISAO_LIMIAR_CONFIANCA}: {zs['cobertura_limiar']:.1%} das fotos ficam acima dele"
        + (f", e nelas a acurácia é {zs['acuracia_acima_limiar']:.1%}." if zs["acuracia_acima_limiar"] is not None else "."),
        "",
        "| Categoria | Precisão | Recall | F1 |",
        "|---|---|---|---|",
    ]
    for c in rotulos:
        r = zs["relatorio"][c]
        md.append(f"| {c} | {r['precision']:.2f} | {r['recall']:.2f} | {r['f1-score']:.2f} |")
    md += ["", "![Matriz zero-shot](visao_matriz_zeroshot.png)"]
    if lp:
        md.append("![Matriz linear probe](visao_matriz_linear_probe.png)")
    if falhas:
        md += ["", "### Casos de falha (fotos noturnas)", "| Arquivo | Esperado | Previsto | Confiança | Acima do limiar |", "|---|---|---|---|---|"]
        md += [f"| {f['arquivo']} | {f['esperado']} | {f['previsto']} | {f['confianca']:.2f} | {'sim' if f['confiavel'] else 'não'} |" for f in falhas]
    (RES / "visao.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:9]))


if __name__ == "__main__":
    main()
