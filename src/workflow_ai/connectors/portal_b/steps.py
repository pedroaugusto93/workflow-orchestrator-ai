from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from workflow_ai.connectors.portal_b.config import PortalBConfig
from workflow_ai.connectors.portal_b.selectors import B
from workflow_ai.domain.models import CaseRecord, ContractLineItem, StepResult
from workflow_ai.ports.browser import BrowserPort, Locator


def _date_br(value: str) -> str:
    raw = str(value or "").strip().split(" ")[0]
    if not raw:
        return ""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt).strftime("%d/%m/%Y")
        except ValueError:
            pass
    return raw


def _year(value: str) -> str:
    normalized = _date_br(value)
    match = re.search(r"(\d{4})$", normalized)
    return match.group(1) if match else ""


def _money4(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "0,0000"
    if "," in raw:
        raw = raw.replace(".", "").replace(",", ".")
    try:
        number = float(raw)
    except ValueError:
        number = 0.0
    text = f"{number:,.4f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def _digits(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _safe_name(value: str) -> str:
    cleaned = re.sub(r'[\\/:*?"<>|\r\n\t]+', "", str(value or ""))
    return re.sub(r"\s+", "_", cleaned).strip("_") or "processo"


@dataclass(slots=True)
class PortalBSteps:
    browser: BrowserPort
    config: PortalBConfig

    def initial_data(self, record: CaseRecord) -> StepResult:
        missing = [
            name
            for name, value in {
                "title": record.title,
                "start_date": record.start_date,
                "end_date": record.end_date or record.commitment_date,
                "object_text": record.object_text,
                "justification": self.config.justification,
            }.items()
            if not str(value or "").strip()
        ]
        if missing:
            return StepResult(ok=False, message="Dados iniciais ausentes: " + ", ".join(missing))

        self.browser.navigate(self.config.target_url)
        existing = self._locate_row(record, open_edit=False)
        if existing:
            return StepResult(
                ok=True,
                message="Pré-cadastro já existente; criação ignorada.",
                external_id=existing,
            )

        self.browser.navigate(self.config.target_url)
        self.browser.click(B.CREATE)
        self.browser.fill(B.TITLE, record.title)
        self._select_option(B.CATEGORY, self.config.category_label)
        self.browser.fill(B.START_DATE, _date_br(record.start_date))
        self.browser.fill(B.END_DATE, _date_br(record.end_date or record.commitment_date))
        self.browser.fill(B.DESCRIPTION, record.object_text)
        self.browser.fill(B.JUSTIFICATION, self.config.justification)
        self.browser.click(B.SAVE_INITIAL)
        self.browser.page_ready()
        return StepResult(ok=True, message="Pré-cadastro criado.")

    def locate(self, record: CaseRecord) -> StepResult:
        self.browser.navigate(self.config.target_url)
        row_id = self._locate_row(record, open_edit=True)
        if not row_id:
            return StepResult(ok=False, message="Contratação não localizada no plano selecionado.")
        return StepResult(ok=True, message="Contratação localizada e aberta.", external_id=row_id)

    def ensure_edit_context(self, record: CaseRecord) -> None:
        if self.browser.exists(B.PROCESS, timeout=1.0):
            return
        self.browser.navigate(self.config.target_url)
        row_id = self._locate_row(record, open_edit=True)
        if not row_id:
            raise RuntimeError("Não foi possível reabrir a contratação para retomada.")

    def basic_data(self, record: CaseRecord) -> StepResult:
        self.browser.fill(B.PROCESS, record.process_id)
        self._select_option(B.CONTRACT_TYPE, self.config.contract_type_label)
        self._select_legal_basis()
        self._select_option(B.DISPUTE_MODE, self.config.dispute_mode_label)
        return StepResult(ok=True, message="Dados básicos preenchidos.")

    def additional_data(self, record: CaseRecord) -> StepResult:
        if not record.source_link:
            return StepResult(ok=False, message="Link do processo eletrônico não informado.")
        self.browser.click(B.ADDITIONAL_TAB)
        self._expand_fieldset("Endereço do Processo Eletrônico")
        checked = self.browser.read_attribute(B.ELECTRONIC_CHECK, "aria-checked", timeout=3).lower()
        if checked != "true":
            self.browser.click(B.ELECTRONIC_LABEL)
        self.browser.fill(B.PROCESS_LINK, record.source_link)

        self._expand_fieldset("Recurso Orçamentário da Contratação")
        root = Locator(
            "xpath",
            "//*[@id='label-tipo-recurso-contratacao']/following::div["
            "contains(concat(' ', normalize-space(@class), ' '), ' p-multiselect ')][1]",
        )
        self.browser.click(root)
        option = Locator(
            "xpath",
            f"//li[@role='option' and (@aria-label='{self.config.resource_label}' "
            f"or .//span[normalize-space(.)='{self.config.resource_label}'])]",
        )
        selected = self.browser.read_attribute(option, "aria-selected", timeout=4).lower()
        if selected != "true":
            self.browser.click(option)
        return StepResult(ok=True, message="Dados adicionais preenchidos.")

    def items(self, record: CaseRecord) -> StepResult:
        items = record.effective_items()
        errors: list[str] = []
        for index, item in enumerate(items, start=1):
            if not _digits(item.supplier_document):
                errors.append(f"item {index}: documento do fornecedor ausente")
            if _money4(item.effective_value) == "0,0000":
                errors.append(f"item {index}: valor vazio/zero")
        if errors:
            return StepResult(ok=False, message="; ".join(errors))
        if not self.config.catalog_code and not self.config.catalog_text:
            return StepResult(ok=False, message="Catálogo não configurado para o Portal B.")

        self.browser.click(B.ITEMS_TAB)
        card_ids = self._card_ids()
        if card_ids and len(card_ids) != len(items):
            return StepResult(
                ok=False,
                message=f"Quantidade de cards divergente: tela={len(card_ids)} esperado={len(items)}.",
            )

        if not card_ids:
            self._create_catalog_items(items)
            self.browser.click(B.CART)
            self.browser.click(B.ADD_TO_DC)
            self.browser.click(B.CONFIRM_DC)
            self.browser.page_ready()
            card_ids = self._card_ids()

        if len(card_ids) != len(items):
            return StepResult(
                ok=False,
                message=f"Após inclusão, cards={len(card_ids)} esperado={len(items)}.",
            )
        self._fill_delivery(card_ids)
        self._fill_results(card_ids, items)
        return StepResult(ok=True, message=f"{len(items)} item(ns) concluído(s).")

    def attachments(self, record: CaseRecord) -> StepResult:
        path = Path(str(record.file_path or "").strip().strip('"').strip("'")) if record.file_path else None
        if not path or not path.is_file():
            return StepResult(ok=False, message="Arquivo do ato autorizativo não encontrado.")
        self.browser.click(B.ATTACHMENTS_TAB)
        self.browser.click(B.CREATE_ATTACHMENT)
        self._select_option(B.ATTACHMENT_TYPE, self.config.attachment_type_label)
        self.browser.upload(B.ATTACHMENT_FILE, path)
        self.browser.click(B.SAVE_ATTACHMENT)
        return StepResult(ok=True, message="Anexo incluído.")

    def responsibles(self, record: CaseRecord) -> StepResult:
        people = [
            (
                record.responsible_document,
                record.responsible_email,
                self.config.responsible_role_label,
            ),
            (
                record.authority_document,
                record.authority_email,
                self.config.authority_role_label,
            ),
        ]
        missing = [role for document, _email, role in people if len(_digits(document)) != 11]
        if missing:
            return StepResult(ok=False, message="CPF ausente/inválido para: " + ", ".join(missing))

        self.browser.click(B.RESPONSIBLES_TAB)
        for document, email, role in people:
            if self._document_visible(document):
                continue
            self.browser.click(B.CREATE_RESPONSIBLE)
            self.browser.fill(B.RESPONSIBLE_DOCUMENT, _digits(document))
            try:
                self.browser.read_value(B.RESPONSIBLE_NAME, timeout=8)
            except Exception:
                return StepResult(ok=False, message=f"Nome não carregado automaticamente para {role}.")
            if email:
                self.browser.fill(B.RESPONSIBLE_EMAIL, email)
            self._select_option(B.RESPONSIBLE_ROLE, role)
            self.browser.click(B.SAVE_RESPONSIBLE)
            self.browser.wait_absent(B.SAVE_RESPONSIBLE, timeout=10)
        return StepResult(ok=True, message="Responsáveis cadastrados.")

    def publish(self, record: CaseRecord) -> StepResult:
        self.browser.click(B.CONCLUDE)
        if not self.browser.exists(B.PUBLISH, timeout=10):
            return StepResult(ok=False, message="Botão de divulgação não apareceu após concluir.")
        self.browser.click(B.PUBLISH)
        if not self.browser.exists(B.CLOSE_RECEIPT, timeout=20):
            return StepResult(ok=False, message="Publicação acionada, mas recibo não apareceu.")
        destination = self.config.receipt_dir / f"{_safe_name(record.process_id)}.pdf"
        receipt = self.browser.print_pdf(destination)
        self.browser.click(B.CLOSE_RECEIPT)
        return StepResult(
            ok=True,
            message="Publicação concluída.",
            metadata={"receipt": str(receipt)},
        )

    def _select_option(self, trigger: Locator, label: str) -> None:
        self.browser.click(trigger)
        self.browser.click(B.option(label))

    def _select_legal_basis(self) -> None:
        self.browser.click(B.LEGAL_EDIT)
        law = B.tree_node(self.config.legal_law_label)
        article = B.tree_node(self.config.legal_article_label)
        for node in (law, article):
            if self.browser.read_attribute(node, "aria-expanded", timeout=5).lower() != "true":
                self.browser.click(
                    Locator(
                        "css",
                        f"{node.value} div.p-treenode-content button.p-tree-toggler",
                    )
                )
        clause = B.tree_prefix(self.config.legal_clause_prefix)
        self.browser.click(Locator("css", f"{clause.value} div.p-treenode-content"))
        self.browser.click(B.LEGAL_SAVE)

    def _expand_fieldset(self, title: str) -> None:
        header = Locator(
            "xpath",
            "//fieldset[contains(@class,'collapsible')]"
            f"[.//legend[contains(normalize-space(.), '{title}')]]"
            "//div[contains(@class,'fieldset-header')]",
        )
        if self.browser.read_attribute(header, "aria-label", timeout=5).strip().lower() == "expandir":
            legend = Locator(
                "xpath",
                "//fieldset[contains(@class,'collapsible')]"
                f"[.//legend[contains(normalize-space(.), '{title}')]]//legend",
            )
            self.browser.click(legend)

    def _select_pca(self, record: CaseRecord) -> None:
        year = _year(record.start_date or record.commitment_date or record.end_date)
        if not year:
            raise RuntimeError("Ano do plano não pôde ser determinado.")
        label = f"PCA {year} - {self.config.pca_status}"
        current = ""
        try:
            current = self.browser.read_text(B.PCA, timeout=2)
        except Exception:
            pass
        if label.casefold() not in current.casefold():
            self._select_option(B.PCA, label)

    def _locate_row(self, record: CaseRecord, *, open_edit: bool) -> str:
        self._select_pca(record)
        try:
            self.browser.click(B.MY_UNIT_TAB, timeout=3)
        except Exception:
            pass
        title = record.title.strip()
        start = _date_br(record.start_date)
        end = _date_br(record.end_date or record.commitment_date)
        row_id = self.browser.execute_script(
            """
            const norm=s=>(s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'')
              .toLowerCase().replace(/\s+/g,' ').trim();
            const [title,start,end,doClick]=arguments;
            for (const tr of document.querySelectorAll("tr[id^='contratacao-']")) {
              const td=tr.querySelectorAll('td');
              if (td.length < 8) continue;
              const screenTitle=norm(td[3].innerText);
              const titleOk=screenTitle===norm(title)||screenTitle.includes(norm(title))||
                norm(title).includes(screenTitle);
              const startOk=(td[6].innerText||'').trim()===start;
              const endOk=(td[7].innerText||'').trim()===end;
              if (titleOk && startOk && endOk) {
                if (doClick) {
                  const link=tr.querySelector('td.link-contratacao');
                  if (link) link.click();
                }
                return tr.id || 'found';
              }
            }
            return '';
            """,
            title,
            start,
            end,
            open_edit,
        ) or ""
        if row_id and open_edit:
            self.browser.click(B.EDIT, timeout=10)
        return row_id

    def _card_ids(self) -> list[str]:
        result = self.browser.execute_script(
            """
            return Array.from(document.querySelectorAll("p-card[id^='item-']"))
              .filter(el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length))
              .map(el => (el.id||'').replace('item-',''))
              .filter(Boolean)
              .sort((a,b)=>(parseInt(a)||0)-(parseInt(b)||0));
            """
        )
        return [str(x) for x in (result or [])]

    def _create_catalog_items(self, items: list[ContractLineItem]) -> None:
        self.browser.click(B.OPEN_CATALOG)
        term = self.config.catalog_code or self.config.catalog_text
        self.browser.fill(B.CATALOG_SEARCH, term)
        self.browser.click(B.CATALOG_SEARCH_BUTTON)
        if not self.browser.exists(B.CATALOG_TABLE, timeout=10):
            raise RuntimeError("Tabela de catálogo não apareceu.")
        for item in items:
            clicked = self.browser.execute_script(
                """
                const [code,description]=arguments;
                for (const tr of document.querySelectorAll('p-table#tbServico tbody tr')) {
                  const td=tr.querySelectorAll('td');
                  const first=(td[0]?.innerText||'').trim();
                  const text=(tr.innerText||'').toLowerCase();
                  const ok=(code && (first===code || text.includes(code.toLowerCase()))) ||
                           (description && text.includes(description.toLowerCase()));
                  if (!ok) continue;
                  const btn=Array.from(tr.querySelectorAll('button'))
                    .find(b=>b.querySelector('i.fa-plus'));
                  if (btn) { btn.click(); return true; }
                }
                return false;
                """,
                self.config.catalog_code,
                self.config.catalog_text,
            )
            if not clicked:
                raise RuntimeError("Serviço configurado não localizado no catálogo.")
            self.browser.fill(B.UNIT_VALUE, _money4(item.effective_value))
            self.browser.click(B.SAVE_ITEM)
            self.browser.wait_absent(B.UNIT_VALUE, timeout=10)

    def _fill_delivery(self, card_ids: list[str]) -> None:
        pending = self.browser.execute_script(
            """
            const ids=arguments[0];
            return ids.filter(id=>{
              const el=document.getElementById('quantidade-total-item-'+id);
              const text=(el?.innerText||'').normalize('NFD')
                .replace(/[\u0300-\u036f]/g,'').toLowerCase();
              return !text || text.includes('nao detalhado');
            });
            """,
            card_ids,
        ) or []
        if not pending:
            return
        if len(pending) == len(card_ids):
            self.browser.click(B.MARK_ALL_ITEMS)
        else:
            self.browser.execute_script(
                """
                for (const id of arguments[0]) {
                  const card=document.getElementById('item-'+id);
                  const cb=card?.querySelector("input[type='checkbox']");
                  if (cb && !cb.checked) cb.click();
                }
                """,
                pending,
            )
        self.browser.click(B.ADD_DELIVERY)
        count = self.browser.execute_script(
            """
            const inputs=Array.from(document.querySelectorAll("input[id^='quantidade-item-']"))
              .filter(el => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length));
            for (const el of inputs) {
              const setter=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
              setter.call(el,'1');
              el.dispatchEvent(new Event('input',{bubbles:true}));
              el.dispatchEvent(new Event('change',{bubbles:true}));
              el.dispatchEvent(new Event('blur',{bubbles:true}));
            }
            return inputs.length;
            """
        ) or 0
        if count != len(pending):
            raise RuntimeError(f"Locais de entrega: linhas={count}, esperadas={len(pending)}.")
        self.browser.click(Locator("css", "button#salvar:not([disabled])"))

    def _fill_results(self, card_ids: list[str], items: list[ContractLineItem]) -> None:
        for card_id, item in zip(card_ids, items):
            panel_id = f"collapseItem-{card_id}"
            expanded = self.browser.execute_script(
                "return (document.getElementById(arguments[0])?.classList.contains('show')) || false;",
                panel_id,
            )
            if not expanded:
                self.browser.click(Locator("id", f"btnExpandirItem{card_id}"))
            self.browser.click(Locator("id", f"tab-resultados-{card_id}"))
            doc = _digits(item.supplier_document)
            exists = self.browser.execute_script(
                """
                const [panelId,doc]=arguments;
                const panel=document.getElementById(panelId);
                const digits=(panel?.innerText||'').replace(/\D/g,'');
                return !!doc && digits.includes(doc);
                """,
                f"tabpanel-resultados-{card_id}",
                doc,
            )
            if exists:
                continue
            self.browser.click(
                Locator("css", f"#tabpanel-resultados-{card_id} button#criar-resultado")
            )
            self.browser.fill(B.RESULT_SUPPLIER, doc)
            self.browser.fill(B.RESULT_VALUE, _money4(item.effective_value))
            self.browser.fill(B.RESULT_QUANTITY, item.quantity or "1")
            self.browser.click(Locator("css", "button#salvar:not([disabled])"))
            self.browser.wait_absent(B.RESULT_SUPPLIER, timeout=10)

    def _document_visible(self, document: str) -> bool:
        digits = _digits(document)
        return bool(
            self.browser.execute_script(
                "return (document.body?.innerText||'').replace(/\D/g,'').includes(arguments[0]);",
                digits,
            )
        )
