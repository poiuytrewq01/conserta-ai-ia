package br.com.consertaai.ia;

import java.util.Map;

/** Resposta do serviço Python ia-visao (POST /visao/classificar-url). */
public record VisaoIA(String categoria, Double confianca, Boolean confiavel, Map<String, Double> scores, String modelo) {
}
