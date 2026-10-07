# Optional private connector overrides

Os conectores oficiais do projeto ficam publicamente em:

- `src/workflow_ai/connectors/portal_a/`
- `src/workflow_ai/connectors/portal_b/`

Esta pasta existe somente para um ambiente que precise **substituir** um conector
sem modificar o código público.

Contrato opcional em `private_connectors/__init__.py`:

```python
from workflow_ai.domain.models import WorkflowKind

def build_connectors():
    return {
        WorkflowKind.PORTAL_A_SUBMISSION: MeuConectorA(...),
        WorkflowKind.PORTAL_B_PUBLICATION: MeuConectorB(...),
    }
```

Não coloque aqui planilhas, documentos, certificados ou dados reais. Como a pasta é
ignorada pelo Git, ela pode conter código/configuração estritamente local quando isso
for necessário, mas o caminho preferencial é manter segredos e valores operacionais
em variáveis de ambiente.
