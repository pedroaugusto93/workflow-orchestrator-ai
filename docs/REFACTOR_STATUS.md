# Status da reescrita

## Fluxo A

Reimplementado na nova arquitetura:

- preparação e retomada de contexto;
- dados básicos;
- itens;
- documentos;
- empenhos;
- conferência pós-gravação;
- envio irreversível protegido pelo approval gate;
- geração de recibo em PDF;
- estado por etapa no SQLite.

A homologação final dos seletores e da retomada exige execução no portal real a partir do agente Windows.

## Fluxo B

Reimplementado estruturalmente na nova arquitetura:

- pré-cadastro com prevenção de duplicidade;
- localização e reabertura da contratação;
- dados básicos;
- dados adicionais;
- múltiplos itens por processo;
- local de entrega;
- resultado individual por fornecedor;
- anexos;
- responsáveis;
- publicação irreversível protegida pelo approval gate;
- geração de recibo em PDF.

O domínio agora trata processo como agregado e os itens como filhos tipados. O SQLite persiste a coleção de itens; a planilha deixou de ser a máquina de estados.

## O que ainda depende do PC

Os dois conectores precisam de homologação contra os portais reais porque Selenium depende do DOM efetivamente carregado, da sessão autenticada, de certificado quando aplicável e do comportamento do navegador.

## Regra arquitetural

Nenhum módulo em `src/` importa código de `legacy/`. Os projetos anteriores são apenas especificação funcional durante a reescrita.
