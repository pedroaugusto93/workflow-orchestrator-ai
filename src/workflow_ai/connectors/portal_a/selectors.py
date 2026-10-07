from __future__ import annotations

from workflow_ai.ports.browser import Locator


class A:
    PROCESS = Locator("css", 'input-text[name="ProcessoAdministrativo"] input')
    TYPOLOGY = Locator("css", 'input-select[name="TipologiaObjetoContratacao"] select')
    PRICE_REGISTRATION = Locator("css", 'input-select[name="registroPreco"] select')
    VALUE = Locator("css", 'input-currency[name="Valor"] input')
    ITEM_LOT = Locator("css", 'input-select[name="TipoLicitacao"] select')
    LEGAL_BASIS = Locator("css", 'input-select[name="FundamentoLegal"] select')
    ORDERING_OFFICER = Locator("css", 'app-pessoa-pesquisa-cadastro[name="cpfCnpjOrdenador"] input[name="cpfCnpj"]')
    ACT_DATE = Locator("css", 'input-date[name="DataAto"] input')
    SUPPLIER_DOCUMENT = Locator("css", 'app-pessoa-pesquisa-cadastro[name="fornecedor"] input[name="cpfCnpj"]')
    SUPPLIER_NAME = Locator("css", 'app-pessoa-pesquisa-cadastro[name="fornecedor"] input-text[name="nomeRazaoSocial"] input')
    EXECUTION_TERM = Locator("css", 'input-number[name="prazoExecucao"] input')
    OBJECT = Locator("css", 'input-textarea[name="Objeto"] textarea')
    SAVE_BASIC = Locator("css", 'button[form="frm"][type="submit"]')
    EXTERNAL_ID = Locator("css", 'input-text[name="id"] input, #input-text-0')

    NEW_ITEM = Locator("xpath", "//button[contains(.,'Incluir Novo Item')]")
    ITEM_POSITION = Locator("name", "posicao")
    ITEM_DESCRIPTION = Locator("css", 'input-textarea[name="Descricao"] textarea')
    ITEM_QUANTITY = Locator("css", 'input-number[name="quantidade"] input')
    ITEM_UNIT = Locator("css", 'input-select[name="unidadeMedida"] select')
    ITEM_UNIT_VALUE = Locator("css", 'input-currency[name="ValorUnitario"] input')
    SAVE_MODAL = Locator("css", ".modal-footer > .actions.ml-0 > button.btn-outline-primary[type='submit']")
    MODAL = Locator("css", ".modal.show")

    NEW_DOCUMENT = Locator("xpath", "//button[contains(normalize-space(.),'Incluir Documento')]")
    DOCUMENT_MODAL = Locator("css", ".modal.show, modal-container[role='dialog']")
    FILE_INPUT = Locator("css", ".modal.show input[type='file'], modal-container[role='dialog'] input[type='file']")
    SAVE_DOCUMENT = Locator("xpath", "//div[contains(@class,'modal-footer')]//button[@type='submit' and contains(@class,'btn-outline-primary')]")

    NEW_COMMITMENT = Locator("xpath", "//div[contains(@class,'tab-footer')]//button[contains(normalize-space(.),'Incluir Empenho')]")
    COMMITMENT_YEAR = Locator("css", ".modal.show input[type='number']")
    COMMITMENT_DATE = Locator("css", ".modal.show input[bsdatepicker]")
    COMMITMENT_UNIT = Locator("css", ".modal.show input[placeholder='000000']")
    COMMITMENT_NUMBER = Locator("css", ".modal.show input[autoselectonfocus][type='text']:not([currencymask]):not([placeholder='000000'])")
    COMMITMENT_VALUE = Locator("css", ".modal.show input[currencymask]")
    SAVE_COMMITMENT = SAVE_DOCUMENT

    ITEM_GRID = Locator("css", "#datagrid-1 tbody")
    DOCUMENT_GRID = Locator("css", "#datagrid-0 tbody")
    COMMITMENT_GRID = Locator("css", "#datagrid-2 tbody")

    SEND = Locator("xpath", "//button[contains(normalize-space(.),'Enviar ao TCE')]")
    SEARCH_PROCESS = Locator("css", 'input-text[name="NumeroProcesso"] input')
    SEARCH_BUTTON = Locator("xpath", "//button[contains(normalize-space(.),'Pesquisar')]")
