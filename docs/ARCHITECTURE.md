# Arquitetura

## Decisão central

O projeto usa arquitetura hexagonal/modular: o domínio não conhece Selenium, Excel,
FastAPI nem um portal concreto. Integrações implementam portas bem definidas.

## Camadas

1. **Domain** — `CaseRecord`, `ContractLineItem`, `Job`, estados e idempotência.
2. **Application** — workflows e `Orchestrator`; decide ordem, retomada e aprovação.
3. **Ports** — contratos de navegador, repositório e conectores.
4. **Infrastructure** — SQLite, adaptador Selenium, settings e carregamento de overrides.
5. **Connectors** — implementações públicas de Portal A e Portal B.
6. **Apps** — API/painel e agente local.

## Processo como agregado

O processo é a unidade de execução. No fluxo B, várias linhas de planilha tornam-se um
único `CaseRecord` com uma coleção de `ContractLineItem`.

Isso permite que estado, idempotência e retomada pertençam ao processo, sem depender
de percentuais gravados em cada linha do Excel.

## Fronteira do navegador

Os conectores dependem de `BrowserPort`, não de `WebDriver` diretamente. O adaptador
`SeleniumBrowser` concentra espera, clique, preenchimento, upload, leitura de atributos
e geração de PDF.

## Código público vs. configuração privada

A lógica dos conectores e os seletores genéricos são públicos. Permanecem fora do Git:

- URLs reais do ambiente;
- credenciais e tokens;
- certificados;
- justificativas/textos que identifiquem a organização;
- planilhas e documentos;
- códigos locais quando forem sensíveis;
- logs e evidências de produção.

`private_connectors/` é apenas um mecanismo opcional de override.

## Por que é melhor que os legados

- `main.py` deixa de concentrar fluxo, navegador e estado;
- progresso deixa de depender da planilha ou de JSON solto;
- a planilha vira fonte de importação;
- cada etapa possui estado persistido e pode ser retomada;
- ações irreversíveis possuem approval gate;
- idempotência é transversal;
- conectores não conhecem UI web nem persistência;
- o código público não precisa conhecer o nome da instituição.

## IA

A IA fica acima dos dados e abaixo das políticas de execução. Pode extrair campos,
sugerir mapeamentos, apontar inconsistências, explicar falhas e escolher workflows
conhecidos.

A IA não pode desativar idempotência, revelar segredos, inventar campos ausentes,
alterar políticas de aprovação ou executar livremente ações irreversíveis.

## Web + agente local

O painel pode ficar hospedado e ser acessado pelo celular. O agente Windows mantém
sessão autenticada do navegador, certificado e acesso de rede. Em implantação remota,
o armazenamento compartilhado deve migrar de SQLite para PostgreSQL/fila transacional.
