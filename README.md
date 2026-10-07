# Workflow Orchestrator AI

Arquitetura aberta e desacoplada para orquestrar automações de processos em múltiplos portais, com painel web responsivo, agente local e execução segura por etapas.

> Este repositório **não contém dados reais, nomes institucionais, URLs operacionais, credenciais, certificados, planilhas de produção nem seletores privados**. Os conectores de produção são carregados externamente por configuração/plug-in local.

## Objetivos

- Unificar dois fluxos de automação sem acoplar os sistemas entre si.
- Preservar os projetos legados de produção sem qualquer alteração.
- Separar domínio, orquestração, persistência, navegador, conectores e interface web.
- Evitar duplicidade com idempotência e estado persistente por etapa.
- Permitir retomada após falhas sem repetir etapas irreversíveis.
- Exigir aprovação antes de ações irreversíveis quando configurado.
- Permitir operação pelo celular através de um painel web, mantendo navegador/certificado no agente Windows.
- Deixar o GitHub público sem expor a organização ou dados operacionais.

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

A IA **não controla o DOM diretamente** em produção. Ela pode classificar, conferir, extrair e sugerir; a execução permanece em workflows determinísticos com guardas, idempotência e auditoria.

## Começar localmente

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
copy .env.example .env   # Windows
# cp .env.example .env  # Linux/macOS
python -m apps.api.main
```

Em outro terminal:

```bash
python -m apps.agent.main
```

Acesse `http://127.0.0.1:8000`.

## Estrutura

```text
apps/
  api/                  # painel e API
  agent/                # executor local/Windows
src/workflow_ai/
  domain/               # entidades e regras puras
  application/          # casos de uso e orquestração
  ports/                 # contratos (interfaces)
  infrastructure/       # SQLite, Selenium, configurações
  connectors/           # interfaces neutras dos portais
  ai/                   # IA assistiva, nunca executor irrestrito
config/                  # somente exemplos públicos
private_connectors/      # ignorado pelo git; implementação operacional local
data/ logs/ artifacts/  # ignorados
```

Leia `docs/ARCHITECTURE.md` e `docs/MIGRATION.md` antes de portar os conectores legados.
