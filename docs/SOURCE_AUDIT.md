# Auditoria inicial dos projetos de origem

Os projetos de produção foram somente lidos. Nenhum arquivo, branch ou configuração deles foi alterado.

## Achados que influenciaram a nova arquitetura

- O fluxo A já possuía boas ideias de anti-duplicidade e retomada, porém o estado era mantido em JSON e o progresso também voltava para planilha.
- O fluxo B já tinha separação por `page_*`, modelo tipado e um orquestrador central, mas ainda concentrava estado operacional na planilha.
- Os dois fluxos dependem de Selenium/Chrome em sessão autenticada, então o navegador foi isolado atrás de conectores e de um agente local.
- Havia artefatos operacionais versionados nos repositórios públicos de origem, como planilha e arquivos de log/diagnóstico. A nova raiz bloqueia esses formatos por padrão no `.gitignore`.
- Constantes, URLs, seletores e textos capazes de identificar o ambiente foram deslocados para configuração/conector privado.

## Regra de migração

O novo projeto recebe cópias adaptadas do comportamento dos legados. Os repositórios antigos não são importados como dependência, submodule, subtree ou package. Isso impede que uma mudança no novo projeto afete produção acidentalmente.
