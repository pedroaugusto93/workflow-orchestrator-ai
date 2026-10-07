# Reescrita dos dois projetos legados

Os projetos anteriores permanecem independentes e intocados. Eles são tratados como
**especificação funcional**: comportamento, validações e seletores úteis são estudados,
mas o runtime novo não importa módulos dos projetos antigos.

## Princípio

Não é uma migração de arquivos para novas pastas. Cada responsabilidade antiga é
reimplementada na arquitetura nova:

- planilha -> importador de dados;
- JSON/percentuais -> `JobRepository`/SQLite;
- `main.py` monolítico -> `Orchestrator` + workflows;
- helpers Selenium espalhados -> `BrowserPort` + `SeleniumBrowser`;
- páginas antigas -> steps dos conectores;
- envio/publicação -> etapa irreversível com approval gate.

## Fluxo A

| Responsabilidade antiga | Implementação nova |
|---|---|
| orquestração do `main.py` | `application/orchestrator.py` + workflow A |
| estado/retomada | SQLite / `job_steps` |
| dados básicos | `connectors/portal_a/steps.py::basic_data` |
| itens | `items` |
| documentos | `documents` |
| empenhos | `commitments` |
| conferência | `verify` |
| envio | `submit` com aprovação |
| recibos | `artifacts/` fora do Git |

## Fluxo B

| Responsabilidade antiga | Implementação nova |
|---|---|
| agrupamento por processo | `CaseRecord.items` + `ContractLineItem` |
| pré-cadastro | `initial_data` com busca antes de criar |
| localizar/reabrir | `locate` / `ensure_edit_context` |
| dados básicos | `basic_data` |
| dados adicionais | `additional_data` |
| itens/local/resultado | `items` |
| anexos | `attachments` |
| responsáveis | `responsibles` |
| publicação | `publish` com aprovação |
| status percentual da planilha | eliminado do runtime; estado fica no SQLite |

## Código público e configuração privada

Os conectores canônicos ficam em `src/workflow_ai/connectors/portal_a` e
`portal_b`. URLs reais, justificativas institucionais, códigos locais, credenciais,
certificados e dados ficam em `.env` ou no ambiente do agente e não são commitados.

`private_connectors/` permanece apenas como mecanismo **opcional de override** para
um ambiente que precise substituir um conector público sem alterar o repositório.

## Homologação

A reescrita estrutural não equivale a homologação Selenium. Antes de substituir os
robôs de produção:

1. executar em ambiente autenticado;
2. validar cada step isoladamente;
3. interromper e retomar jobs em pontos diferentes;
4. confirmar anti-duplicidade;
5. comparar os registros gerados com os robôs atuais;
6. testar ações irreversíveis somente com aprovação explícita;
7. só então descontinuar o legado.
