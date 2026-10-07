# Private connector pack

Esta pasta é ignorada pelo Git e deve existir somente no ambiente operacional.

Contrato mínimo em `private_connectors/__init__.py`:

```python
from workflow_ai.domain.models import WorkflowKind

def build_connectors():
    return {
        WorkflowKind.PORTAL_A_SUBMISSION: PortalAConnector(...),
        WorkflowKind.PORTAL_B_PUBLICATION: PortalBConnector(...),
    }
```

Migre para cá a lógica Selenium específica dos dois projetos antigos. URLs, seletores,
textos institucionais, certificados, caminhos e dados reais não devem ser commitados.
