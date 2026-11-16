"""Baixa o conjunto de teste de fotos do Wikimedia Commons, com fonte e licença.

Por que Wikimedia Commons: todas as imagens têm licença livre (CC / domínio
público) e a API devolve autor e licença de cada arquivo, então o manifesto
já sai pronto para o README (requisito "fonte e licença documentadas").

Uso:
    python avaliacao/baixar_fotos.py --por-categoria 20

Saída:
    avaliacao/dados/fotos/<pasta>/<arquivo>.jpg   (fora do git)
    avaliacao/dados/manifest_fotos.csv           (no git: arquivo, categoria, autor, licença, link)

Fotos tiradas pelo grupo: coloque em avaliacao/dados/fotos_grupo/<pasta>/
(ex.: fotos_grupo/buraco/rua_x.jpg). Elas entram no manifesto como fonte "grupo".
"""
from __future__ import annotations

import argparse
import csv
import html
import re
import time
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parent
PASTA_FOTOS = RAIZ / "dados" / "fotos"
PASTA_GRUPO = RAIZ / "dados" / "fotos_grupo"
MANIFESTO = RAIZ / "dados" / "manifest_fotos.csv"
API = "https://commons.wikimedia.org/w/api.php"
HEADERS = {"User-Agent": "ConsertaAi-GS-FIAP/1.0 (projeto academico; avaliacao de modelo)"}

# pasta -> (categoria do app, buscas no Commons em ordem de preferência)
BUSCAS = {
    "buraco": ("Buraco", ["incategory:Potholes", "pothole road", "pothole street"]),
    "iluminacao": ("Iluminação", ["incategory:Street_lights", "street lamp pole", "broken street light"]),
    "lixo": ("Lixo", ["incategory:Litter", "illegal dumping street", "garbage bags sidewalk"]),
    "calcada": ("Calçada", ["broken sidewalk", "damaged sidewalk", "cracked sidewalk"]),
    "sinalizacao": ("Sinalização", ["incategory:Road_signs_in_Brazil", "damaged road sign", "traffic sign street"]),
    "outros": ("Outros", ["empty residential street", "clean street daytime"]),
    # casos de falha (não entram nas métricas principais)
    "falha_noturna": ("Buraco", ["pothole at night", "road at night street"]),
}
PASTAS_FALHA = {"falha_noturna"}


def buscar(termo: str, limite: int = 50) -> list[dict]:
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"{termo} filetype:bitmap", "gsrnamespace": 6, "gsrlimit": limite,
        "prop": "imageinfo", "iiprop": "url|extmetadata|mime", "iiurlwidth": 512,
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    paginas = r.json().get("query", {}).get("pages", {}).values()
    return sorted(paginas, key=lambda p: p.get("index", 0))


def limpar_html(txt: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", txt or "")).strip()[:120]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--por-categoria", type=int, default=20)
    ap.add_argument("--falhas", type=int, default=6)
    args = ap.parse_args()

    linhas, vistos = [], set()
    for pasta, (categoria, termos) in BUSCAS.items():
        alvo = args.falhas if pasta in PASTAS_FALHA else args.por_categoria
        destino = PASTA_FOTOS / pasta
        destino.mkdir(parents=True, exist_ok=True)
        n = 0
        for termo in termos:
            if n >= alvo:
                break
            try:
                paginas = buscar(termo)
            except requests.RequestException as e:
                print(f"  ! busca '{termo}' falhou: {e}")
                continue
            for p in paginas:
                if n >= alvo:
                    break
                info = (p.get("imageinfo") or [{}])[0]
                if p["title"] in vistos or info.get("mime") not in ("image/jpeg", "image/png"):
                    continue
                meta = info.get("extmetadata", {})
                licenca = limpar_html(meta.get("LicenseShortName", {}).get("value", ""))
                if not licenca:
                    continue  # sem licença clara = não usamos
                url = info.get("thumburl") or info.get("url")
                nome = re.sub(r"[^\w.-]", "_", p["title"].removeprefix("File:"))[:80]
                if not nome.lower().endswith((".jpg", ".jpeg", ".png")):
                    nome += ".jpg"
                try:
                    img = requests.get(url, headers=HEADERS, timeout=30)
                    img.raise_for_status()
                except requests.RequestException:
                    continue
                (destino / nome).write_bytes(img.content)
                vistos.add(p["title"])
                n += 1
                linhas.append({
                    "arquivo": f"fotos/{pasta}/{nome}", "pasta": pasta, "categoria": categoria,
                    "conjunto": "falha" if pasta in PASTAS_FALHA else "teste",
                    "fonte": "Wikimedia Commons", "busca": termo,
                    "autor": limpar_html(meta.get("Artist", {}).get("value", "")),
                    "licenca": licenca, "link": info.get("descriptionurl", ""),
                })
                time.sleep(0.2)  # educação com a API
        print(f"{pasta:15s} {n:3d} fotos")

    # fotos do grupo
    if PASTA_GRUPO.exists():
        for f in sorted(PASTA_GRUPO.glob("*/*")):
            if f.suffix.lower() in (".jpg", ".jpeg", ".png") and f.parent.name in BUSCAS:
                linhas.append({
                    "arquivo": f"fotos_grupo/{f.parent.name}/{f.name}", "pasta": f.parent.name,
                    "categoria": BUSCAS[f.parent.name][0],
                    "conjunto": "falha" if f.parent.name in PASTAS_FALHA else "teste",
                    "fonte": "grupo", "busca": "", "autor": "Equipe Conserta Aí", "licenca": "uso acadêmico", "link": "",
                })

    if not linhas:
        raise SystemExit("Nenhuma imagem baixada. Verifique a internet e rode de novo.")
    with MANIFESTO.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)
    print(f"\nManifesto: {MANIFESTO} ({len(linhas)} imagens)")


if __name__ == "__main__":
    main()
