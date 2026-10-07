from __future__ import annotations

from workflow_ai.ports.browser import Locator


class B:
    CREATE = Locator("css", "#criar-contratacao")
    TITLE = Locator("css", "#titulo-contratacao")
    CATEGORY = Locator("css", "#categoria-contratacao")
    START_DATE = Locator("css", "#data-inicio-contratacao")
    END_DATE = Locator("css", "#data-fim-contratacao")
    DESCRIPTION = Locator("css", "#descricao-contratacao")
    JUSTIFICATION = Locator("css", "#justificativa-contratacao")
    SAVE_INITIAL = Locator("css", "#salvar-contratacao")

    PCA = Locator("css", "#input-pca")
    MY_UNIT_TAB = Locator("css", "#contratacoes-minhauasg")
    GRID_ROWS = Locator("css", "tr[id^='contratacao-']")
    EDIT = Locator("xpath", "//button[normalize-space(.)='Editar contratação']")

    PROCESS = Locator("css", "#processo-contratacao")
    CONTRACT_TYPE = Locator("css", "#tipo-contratacao")
    DISPUTE_MODE = Locator("css", "#modo-disputa-contratacao")
    LEGAL_EDIT = Locator(
        "css", "#edicao-fundamento-contratacao em.fa-pencil-square-o, em.fa-pencil-square-o"
    )
    LEGAL_SAVE = Locator("css", "#salvar-fundamento")

    ADDITIONAL_TAB = Locator(
        "xpath",
        "//button[contains(@class,'botao-campo-secao-menu-lateral')]"
        "[.//span[normalize-space(.)='2. Dados adicionais da contratação']]",
    )
    ELECTRONIC_CHECK = Locator("id", "checkbox-tem-link-processo")
    ELECTRONIC_LABEL = Locator("css", "label[for='checkbox-tem-link-processo']")
    PROCESS_LINK = Locator("id", "processo-eletronico-contratacao")
    RESOURCE_LABEL = Locator("id", "label-tipo-recurso-contratacao")

    ITEMS_TAB = Locator(
        "xpath",
        "//button[contains(@class,'botao-campo-secao-menu-lateral')]"
        "[.//span[normalize-space(.)='3. Itens/Grupos'] "
        "or contains(normalize-space(.), '3. Itens/Grupos')]",
    )
    OPEN_CATALOG = Locator("id", "abrir-catalogo")
    CATALOG_SEARCH = Locator(
        "css", "input[placeholder='Digite aqui o material ou serviço a ser pesquisado']"
    )
    CATALOG_SEARCH_BUTTON = Locator("id", "pesquisar-palavra")
    CATALOG_TABLE = Locator("css", "p-table#tbServico")
    UNIT_VALUE = Locator("id", "valor-unitario")
    SAVE_ITEM = Locator("id", "adicionar-item")
    CART = Locator("id", "ir-carrinho")
    ADD_TO_DC = Locator("id", "adicionar-itens")
    CONFIRM_DC = Locator("id", "confirmar")
    CARDS = Locator("css", "p-card[id^='item-']")
    MARK_ALL_ITEMS = Locator("css", "input[aria-labelledby='label-marcar-todos-itens']")
    ADD_DELIVERY = Locator(
        "xpath", "//button[contains(normalize-space(.), 'Adicionar Locais de Entrega')]"
    )
    RESULT_SUPPLIER = Locator("id", "id-fornecedor")
    RESULT_VALUE = Locator("id", "valor")
    RESULT_QUANTITY = Locator("id", "quantidade")

    ATTACHMENTS_TAB = Locator(
        "xpath",
        "//button[contains(@class,'botao-campo-secao-menu-lateral')]"
        "[.//span[normalize-space(.)='4. Anexos']]",
    )
    CREATE_ATTACHMENT = Locator("id", "criar-anexo")
    ATTACHMENT_TYPE = Locator("id", "tipo-anexo")
    ATTACHMENT_FILE = Locator("css", "input[type='file']")
    SAVE_ATTACHMENT = Locator("id", "salvar-anexo")

    RESPONSIBLES_TAB = Locator(
        "xpath",
        "//button[contains(@class,'botao-campo-secao-menu-lateral')]"
        "[.//span[normalize-space(.)='5. Responsáveis']]",
    )
    CREATE_RESPONSIBLE = Locator("id", "criar-responsavel")
    RESPONSIBLE_DOCUMENT = Locator("id", "cpf-responsavel")
    RESPONSIBLE_NAME = Locator("id", "nome-responsavel")
    RESPONSIBLE_EMAIL = Locator("id", "email-responsavel")
    RESPONSIBLE_ROLE = Locator(
        "css",
        "p-dropdown#cargo-funcao-responsavel "
        "span[role='combobox'][aria-labelledby='label-cargo-funcao-responsavel']",
    )
    SAVE_RESPONSIBLE = Locator("id", "salvar-responsavel")

    CONCLUDE = Locator("id", "concluir-contratacao")
    PUBLISH = Locator("xpath", "//button[normalize-space(.)='Divulgar a contratação']")
    CLOSE_RECEIPT = Locator("xpath", "//button[normalize-space(.)='FECHAR']")

    @staticmethod
    def option(label: str) -> Locator:
        return Locator("css", f"li[role='option'][aria-label='{label}']")

    @staticmethod
    def tree_node(label: str) -> Locator:
        return Locator("css", f"li[role='treeitem'][aria-label='{label}']")

    @staticmethod
    def tree_prefix(prefix: str) -> Locator:
        return Locator("css", f"li[role='treeitem'][aria-label^='{prefix}']")
