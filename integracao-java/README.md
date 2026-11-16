# Integração com a API Java (Spring AI)

Arquivos de exemplo para a API Java usar a IA dentro do consumer de `ocorrencia.criada`:

| Arquivo | O que faz |
|---|---|
| `TriagemIA.java` | record da saída estruturada do LLM |
| `VisaoIA.java` | record da resposta do ia-visao |
| `IaVisaoClient.java` | chama `POST /visao/classificar-url` do serviço Python |
| `TriagemIAService.java` | visão + LLM (Spring AI + `BeanOutputConverter`) com fallback |
| `application-ia.properties` | Spring AI apontando para o Gemini (chave por variável de ambiente) |

Copie também `prompts/triagem_sistema.txt` para `src/main/resources/prompts/`.

Uso no consumer:

```java
@RabbitListener(queues = "ocorrencia.criada")
public void aoCriar(OcorrenciaCriadaEvent ev) {
    TriagemIA t = triagemIAService.triar(ev.descricao(), ev.categoria(), ev.fotoUrl());
    ocorrenciaService.gravarResultadoIA(ev.id(), t);  // resumo_ia, categoria_sugerida_ia, prioridade
}
```

O evento leva só id, descrição, categoria e URL da foto. Nome, email e coordenada não entram.
