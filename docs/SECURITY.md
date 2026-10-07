# Segurança e privacidade

- O GitHub público contém código e seletores genéricos, mas não configuração operacional.
- Nunca commitar `.env`, certificados, dados pessoais, planilhas, PDFs, recibos,
  screenshots, dumps HTML ou logs de produção.
- URLs reais, textos institucionais, códigos locais sensíveis e outros valores do
  ambiente devem entrar por variável de ambiente.
- Se um ambiente exigir lógica que não possa ser pública, use o mecanismo opcional
  `private_connectors/` como override; ele não é a implementação principal.
- `robots.txt` e `X-Robots-Tag` reduzem indexação, mas não são autenticação.
- O painel exige autenticação; em ambiente real, use HTTPS e credenciais fortes.
- Para internet pública, prefira VPN/Zero Trust ou autenticação corporativa.
- O agente local deve usar token separado do usuário web.
- Ações irreversíveis exigem aprovação por padrão.
- `ALLOW_FORCE_REPROCESS=false` deve permanecer assim em produção.
- Logs devem mascarar documentos, e-mails e identificadores pessoais.
- O agente é a única camada que deve tocar sessão autenticada, certificados e arquivos
  operacionais locais.
