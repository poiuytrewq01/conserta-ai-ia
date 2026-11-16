package br.com.consertaai.ia;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.converter.BeanOutputConverter;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

/**
 * Triagem com Spring AI. Usa o MESMO prompt do repositório de IA (prompts/triagem_sistema.txt,
 * copiado para src/main/resources/prompts/). Nunca envia nome, email ou coordenada ao LLM.
 */
@Service
public class TriagemIAService {

    private static final Logger log = LoggerFactory.getLogger(TriagemIAService.class);
    private static final List<String> CATEGORIAS = List.of("Buraco", "Iluminação", "Lixo", "Calçada", "Sinalização", "Outros");
    private static final double LIMIAR_FOTO = 0.5;

    private final ChatClient chat;
    private final IaVisaoClient visao;
    private final ObjectMapper json = new ObjectMapper();
    private final BeanOutputConverter<TriagemIA> conversor = new BeanOutputConverter<>(TriagemIA.class);
    private final String promptSistema;

    public TriagemIAService(ChatClient.Builder builder, IaVisaoClient visao) throws Exception {
        this.chat = builder.build();
        this.visao = visao;
        this.promptSistema = new ClassPathResource("prompts/triagem_sistema.txt").getContentAsString(StandardCharsets.UTF_8);
    }

    /** Chamado pelo consumer de "ocorrencia.criada". Nunca lança exceção: o fluxo não trava por causa da IA. */
    public TriagemIA triar(String descricao, String categoriaCidadao, String fotoUrl) {
        String catFoto = null;
        Double confFoto = null;
        try {
            if (fotoUrl != null) {
                VisaoIA v = visao.classificar(fotoUrl);
                if (v != null && v.confianca() != null && v.confianca() >= LIMIAR_FOTO) {
                    catFoto = v.categoria();
                    confFoto = v.confianca();
                }
            }
        } catch (Exception e) {
            log.warn("ia-visao indisponível, seguindo só com a descrição: {}", e.getMessage());
        }
        try {
            Map<String, Object> entrada = new LinkedHashMap<>();
            entrada.put("descricao", descricao);
            entrada.put("categoria_cidadao", categoriaCidadao);
            entrada.put("categoria_foto", catFoto);
            entrada.put("confianca_foto", confFoto);
            String resposta = chat.prompt()
                    .system(promptSistema)
                    .user(json.writeValueAsString(entrada))
                    .call()
                    .content();
            TriagemIA t = conversor.convert(resposta.replace("```json", "").replace("```", "").trim());
            if (t == null || !CATEGORIAS.contains(t.categoriaFinal()) || t.prioridade() == null
                    || t.prioridade() < 1 || t.prioridade() > 5) {
                throw new IllegalStateException("saída fora do contrato: " + resposta);
            }
            return t;
        } catch (Exception e) {
            log.warn("LLM falhou, usando fallback: {}", e.getMessage());
            // Regra do plano: categoria do cidadão e prioridade padrão 3
            return new TriagemIA(categoriaCidadao, 3, null, "Triagem automática indisponível.");
        }
    }
}
