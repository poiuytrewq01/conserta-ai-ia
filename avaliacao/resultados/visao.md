## Resultados - Visão computacional
Modelo: `openai/clip-vit-base-patch32` | 120 fotos de teste | por categoria: {'Buraco': 20, 'Iluminação': 20, 'Lixo': 20, 'Calçada': 20, 'Sinalização': 20, 'Outros': 20}

| Abordagem | Acurácia | F1 macro |
|---|---|---|
| CLIP zero-shot | 72.5% | 0.721 |
| Linear probe (5-fold) | 83.3% | 0.831 |

Limiar de confiança 0.5: 85.0% das fotos ficam acima dele, e nelas a acurácia é 76.5%.

| Categoria | Precisão | Recall | F1 |
|---|---|---|---|
| Buraco | 0.71 | 0.60 | 0.65 |
| Iluminação | 0.77 | 0.85 | 0.81 |
| Lixo | 0.77 | 0.85 | 0.81 |
| Calçada | 0.61 | 0.55 | 0.58 |
| Sinalização | 0.76 | 0.80 | 0.78 |
| Outros | 0.70 | 0.70 | 0.70 |

![Matriz zero-shot](visao_matriz_zeroshot.png)
![Matriz linear probe](visao_matriz_linear_probe.png)

### Casos de falha (fotos noturnas)
| Arquivo | Esperado | Previsto | Confiança | Acima do limiar |
|---|---|---|---|---|
| fotos/falha_noturna/I-205_temporary_pothole_repair.jpg | Buraco | Buraco | 1.00 | sim |
| fotos/falha_noturna/Preparing_to_repair_a_pothole_on_I-205.jpg | Buraco | Buraco | 0.99 | sim |
| fotos/falha_noturna/Night_work__30277711982_.jpg | Buraco | Buraco | 0.83 | sim |
| fotos/falha_noturna/Night_paving__30358099986_.jpg | Buraco | Buraco | 0.90 | sim |
