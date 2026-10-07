# Implantação

## Modo 1 — homologação totalmente local

API e agente rodam no mesmo Windows e compartilham o SQLite.

```text
Browser local -> API local -> SQLite <- agente local -> Chrome/Selenium
```

No `.env` do agente:

```env
AGENT_API_URL=
DATABASE_URL=sqlite:///./data/app.db
```

É o modo mais simples para homologar os conectores sem alterar os robôs antigos.

## Modo 2 — painel hospedado + agente Windows

O painel/API pode ficar em um host HTTPS acessível pelo celular. O agente Windows não
precisa expor porta para a internet: ele inicia conexões de saída e faz polling da API.

```text
Celular
   |
 HTTPS
   v
API/painel hospedado ---- fila/estado
   ^
   | HTTPS + X-Agent-Token
   |
Agente Windows -> Chrome/Selenium -> portais
```

No `.env` do agente Windows:

```env
AGENT_API_URL=https://seu-endereco-da-api
AGENT_TOKEN=um-token-longo-e-aleatorio
```

Na API hospedada, configure o mesmo `AGENT_TOKEN`.

Para uma implantação pequena e de uma única instância, a API pode inicialmente manter
SQLite em armazenamento persistente. Antes de escalar para múltiplas instâncias,
migre a implementação do `JobRepository` para PostgreSQL/fila transacional.

## Modo 3 — produção endurecida

- HTTPS obrigatório;
- SSO/Entra ID ou gateway Zero Trust para usuários;
- PostgreSQL e fila transacional;
- auditoria imutável de eventos;
- segredos em secret manager;
- RBAC;
- telemetria sem PII;
- backups e política de retenção;
- rotação do token do agente.

`noindex` reduz descoberta por buscadores; não use isso como mecanismo de segurança.

## Observação importante

O navegador autenticado, certificados e arquivos locais continuam no agente Windows.
O servidor web recebe somente os dados necessários à fila e ao acompanhamento. Antes
de uso institucional, a arquitetura de hospedagem e os dados enviados à API devem ser
validados conforme as regras de segurança/LGPD do ambiente.
