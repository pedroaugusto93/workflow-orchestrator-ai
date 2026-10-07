# Workflow Orchestrator AI

Arquitetura aberta e desacoplada para orquestrar automações de processos em múltiplos portais, com painel web responsivo, agente local e execução segura por etapas.

> O código dos conectores faz parte do projeto público. Dados reais, nome da organização, URLs operacionais, credenciais, certificados, planilhas de produção e configurações locais ficam fora do Git.

## Objetivos

- Unificar dois fluxos de automação sem acoplar os sistemas entre si.
- Preservar os projetos legados de produção sem qualquer alteração.
- Separar domínio, orquestração, persistência, navegador, conectores e interface web.
- Evitar duplicidade com idempotência e estado persistente por etapa.
- Permitir retomada após falhas sem depender de percentuais gravados em planilha.
- Exigir aprovação antes de ações irreversíveis.
- Permitir operação pelo celular através de painel web, mantendo navegador/certificado no agente Windows.
- Manter o repositório público sem expor dados ou configuração institucional.

## Arquitetura

```text
Celular / navegador
       |
       v
+----------------------+       HTTPS        +----------------------+
|   Web/API (FastAPI)  | <----------------> |   Agente Windows     |
| fila + estado + UI   |                    | Selenium + certificado|
+----------+-----------+                    +----------+-----------+
           |                                           |
           v                                           v
       SQLite/Postgres                         Conector Portal A/B
           |                                           |
           +-------------------+-----------------------+
                               v
                      Orquestrador determinístico
                      + regras + IA assistiva
```

A IA não controla o DOM livremente em produção. Ela pode classificar, conferir, extrair e sugerir; a execução dos portais continua em workflows determinísticos, com idempotência, retomada e aprovação para ações irreversíveis.

## Estrutura

```text
apps/
  api/                  # painel e API
  agent/                # executor local/Windows
src/workflow_ai/
  domain/               # entidades e regras puras
  application/          # workflows e orquestração
  ports/                 # interfaces
  infrastructure/       # SQLite, Selenium e settings
  connectors/
    portal_a/           # conector público do fluxo A
    portal_b/           # conector público do fluxo B
  ai/                   # política da IA assistiva
scripts/
  import_excel.py       # transforma planilha em jobs
  run_agent.ps1
  security_scan.py
data/ logs/ artifacts/  # runtime, ignorados pelo Git
```

## Instalação local

SQLite não precisa ser instalado separadamente; o Python já fornece o módulo `sqlite3`.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
```

Configure o `.env` somente na máquina do agente. Não envie esse arquivo ao GitHub.

## Importar a planilha para a fila

Fluxo A mantém uma execução por registro:

```bash
python scripts/import_excel.py cadastro.xlsx --workflow portal_a_submission
```

Fluxo B agrupa automaticamente todas as linhas do mesmo processo em um único job com vários itens:

```bash
python scripts/import_excel.py cadastro.xlsx --workflow portal_b_publication
```

## Executar

Painel/API:

```bash
python -m apps.api.main
```

Agente local, em outro terminal:

```bash
python -m apps.agent.main
```

Acesse `http://127.0.0.1:8000`.

Consulte também `docs/ARCHITECTURE.md`, `docs/REFACTOR_STATUS.md` e `docs/SECURITY.md`.
