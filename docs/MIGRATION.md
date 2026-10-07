# Plano de migração dos dois projetos legados

Os repositórios de produção permanecem independentes e intocados. A migração é por
**cópia controlada e reescrita**, nunca por importação deles em runtime.

## Mapeamento do legado A

| Legado | Destino novo |
|---|---|
| `main.py` | `application/workflows.py` + conector privado |
| `config.py` | `.env` + arquivo TOML privado |
| `state.py` | `infrastructure/sqlite_repo.py` |
| `planilha_status.py` | estado persistente + exportador opcional |
| `page_dados_basicos.py` | etapa `basic_data` do Portal A |
| `page_itens.py` | etapa `items` |
| `page_documentos.py` | etapa `documents` |
| `page_empenhos.py` | etapa `commitments` |
| `verify.py` | etapa `verify` |
| `page_enviar.py` | etapa irreversível `submit` |
| recibos/PDF | `artifacts/` fora do Git |

## Mapeamento do legado B

| Legado | Destino novo |
|---|---|
| `main.py` | `application/workflows.py` |
| `models.py` | `domain/models.py` |
| `helpers.py` | `importers/excel.py` |
| `pncp_status.py` | SQLite + idempotência por etapa |
| `driver.py` | `infrastructure/browser.py` |
| `app_selectors.py` | configuração privada do Portal B |
| `page_localizar_processo.py` | etapa `locate` |
| `page_dados_basicos.py` | etapa `basic_data` |
| `page_dados_adicionais.py` | etapa `additional_data` |
| `page_itens.py` | etapa `items` |
| `page_anexos.py` | etapa `attachments` |
| `page_responsaveis.py` | etapa `responsibles` |
| `page_publicacao.py` | etapa irreversível `publish` |

## Ordem recomendada de portabilidade

1. Copiar as funções Selenium do legado para `private_connectors/` sem alterar lógica.
2. Adaptar assinatura para `run_step(step_name, record)`.
3. Substituir acesso direto à planilha por `CaseRecord`.
4. Substituir status em Excel/JSON por `JobRepository`.
5. Colocar envio/publicação atrás de approval gate.
6. Rodar primeiro em modo de leitura/dry-run.
7. Comparar resultados com os projetos atuais antes de ativar ações irreversíveis.

A arquitetura nova deve poder rodar lado a lado com os legados até a homologação completa.
