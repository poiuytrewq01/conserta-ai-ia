"""Categorias do Conserta Aí e os rótulos (prompts) usados pelo CLIP.

Os nomes batem com a tabela CATEGORIA do banco Oracle.
Os rótulos ficam em inglês porque o CLIP foi treinado com legendas em inglês;
em português a acurácia cai bastante.

Cada categoria tem VÁRIOS rótulos (prompt ensembling): a média dos embeddings
de texto representa melhor a categoria do que uma frase só.
"""

CATEGORIAS = ["Buraco", "Iluminação", "Lixo", "Calçada", "Sinalização", "Outros"]

ROTULOS_CLIP = {
    "Buraco": [
        "a photo of a pothole on a street",
        "a photo of a damaged asphalt road with a hole",
        "a photo of a large pothole filled with water on the road",
    ],
    "Iluminação": [
        "a photo of a street light pole",
        "a photo of a broken street lamp",
        "a photo of a lamp post on a city street",
    ],
    "Lixo": [
        "a photo of garbage dumped on the street",
        "a photo of trash bags piled on the sidewalk",
        "a photo of litter and rubbish in a public place",
    ],
    "Calçada": [
        "a photo of a broken sidewalk",
        "a photo of a cracked pedestrian pavement with loose tiles",
        "a photo of an uneven damaged sidewalk",
    ],
    "Sinalização": [
        "a photo of a traffic sign",
        "a photo of a damaged road sign",
        "a photo of faded road markings and a street sign",
    ],
    # "Outros" = foto sem problema de zeladoria reconhecível.
    # Serve para o caso de falha "foto sem problema nenhum".
    "Outros": [
        "a photo of a clean street in good condition",
        "a photo of a person",
        "a photo of an indoor room",
    ],
}
