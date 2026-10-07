# Segurança e privacidade

- O GitHub público contém somente código genérico.
- Nunca commitar `.env`, certificados, dados pessoais, planilhas, PDFs, recibos, screenshots,
  dumps HTML ou logs de produção.
- URLs e seletores que identifiquem sistemas operacionais devem ficar no connector pack
  privado quando a discrição for requisito.
- `robots.txt` e `X-Robots-Tag` evitam indexação do painel, mas **não são autenticação**.
- O painel exige autenticação; em ambiente real, use HTTPS e credenciais fortes.
- Para internet pública, prefira VPN/Zero Trust ou autenticação corporativa.
- O agente local deve usar token separado do usuário web.
- Ações irreversíveis exigem aprovação por padrão.
- `ALLOW_FORCE_REPROCESS=false` deve permanecer assim em produção.
- Logs devem mascarar documentos, e-mails e identificadores pessoais.
