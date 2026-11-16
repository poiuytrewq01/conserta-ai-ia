package br.com.consertaai.ia;

import java.util.Map;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

/** Chama o serviço Python ia-visao. A URL vem de variável de ambiente IA_VISAO_URL. */
@Component
public class IaVisaoClient {

    private final RestClient http;

    public IaVisaoClient(@Value("${IA_VISAO_URL:http://localhost:8000}") String baseUrl) {
        this.http = RestClient.builder().baseUrl(baseUrl).build();
    }

    public VisaoIA classificar(String fotoUrl) {
        return http.post().uri("/visao/classificar-url")
                .body(Map.of("foto_url", fotoUrl))
                .retrieve()
                .body(VisaoIA.class);
    }
}
