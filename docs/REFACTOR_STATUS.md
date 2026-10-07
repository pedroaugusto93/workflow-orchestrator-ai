# Status da reescrita

## Fluxo A

Reimplementado na nova arquitetura:

- preparação de contexto;
- dados básicos;
- itens;
- documentos;
- empenhos;
- conferência pós-gravação;
- envio irreversível protegido pelo approval gate;
- geração de recibo por PDF via navegador;
- estado e retomada controlados pelo `JobRepository`, não pela planilha.

A etapa de retomada já recebe o `external_id` do job. A abertura automática de um registro existente a partir da tela de consulta ainda precisa de validação no portal real antes de ser considerada homologada.

## Fluxo B

Ainda usa apenas o workflow abstrato/demo. A próxima fase é reconstruir suas etapas sobre a mesma `BrowserPort`.

## Regra

Nenhum módulo em `src/` pode importar código de `legacy/`.
