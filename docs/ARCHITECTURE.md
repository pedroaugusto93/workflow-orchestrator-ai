# Arquitetura

## Decisão central

O projeto usa arquitetura hexagonal/modular: o domínio não conhece Selenium, Excel,
FastAPI nem um portal concreto. Integrações implementam portas bem definidas.

## Camadas

1. **Domain** — `CaseRecord`, `Job`, estados e chave de idempotência.
2. **Application** — workflow e `Orchestrator`; decide ordem, retomada e aprovação.
3. **Ports** — contratos para repositório e conectores.
4. **Infrastructure** — SQLite, Selenium, settings, carregamento de plug-ins.
5. **Connectors** — implementação específica de cada portal, fora do repositório público.
6. **Apps** — API/painel e agente local.

## Por que é melhor que os legados

- `main.py` deixa de concentrar regra de fluxo e tratamento de erro.
- progresso deixa de depender da planilha ou de JSON solto;
- a planilha vira **fonte de importação**, não banco de dados;
- cada etapa possui estado próprio e pode ser retomada;
- ações irreversíveis possuem approval gate;
- idempotência é transversal aos dois fluxos;
- conectores de portais não conhecem UI web nem persistência;
- o código público não precisa conhecer o nome da instituição.

## IA

A IA fica acima dos dados e abaixo das políticas de execução. Usos adequados:

- extrair campos de documentos;
- sugerir mapeamento de colunas;
- apontar inconsistências antes da execução;
- explicar falhas e sugerir correções;
- escolher um workflow conhecido;
- gerar um plano que será convertido em passos permitidos.

A IA não pode:

- desativar idempotência;
- clicar diretamente em publicação/envio irreversível;
- revelar segredos;
- inventar campos ausentes;
- alterar políticas de aprovação.

## Web + agente local

O painel pode ficar hospedado e ser acessado pelo celular. O agente local mantém a sessão
do navegador, certificado e acesso de rede. Em produção remota, substitua SQLite por
PostgreSQL e use uma fila transacional/worker dedicado.
