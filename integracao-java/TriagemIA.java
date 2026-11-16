package br.com.consertaai.ia;

import com.fasterxml.jackson.annotation.JsonProperty;

/** Saída estruturada do LLM. O BeanOutputConverter transforma o JSON neste record. */
public record TriagemIA(
        @JsonProperty("categoria_final") String categoriaFinal,
        @JsonProperty("prioridade") Integer prioridade,
        @JsonProperty("resumo_tecnico") String resumoTecnico,
        @JsonProperty("justificativa") String justificativa) {
}
