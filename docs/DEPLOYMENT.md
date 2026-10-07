# Implantação

## Fase 1 — local/homologação

API e agente usam o mesmo SQLite e rodam no Windows. Ideal para validar a nova arquitetura
sem alterar os robôs de produção.

## Fase 2 — painel hospedado

- API em host HTTPS privado/público autenticado.
- PostgreSQL gerenciado.
- Agente Windows faz polling autenticado da fila e executa Selenium localmente.
- Celular acessa apenas o painel.

## Fase 3 — produção endurecida

- SSO/Entra ID ou gateway Zero Trust.
- PostgreSQL + fila transacional.
- auditoria imutável de eventos;
- segredo em secret manager;
- RBAC;
- telemetria sem PII;
- backups e política de retenção.

`noindex` reduz descoberta por buscadores; não use isso como mecanismo de segurança.
