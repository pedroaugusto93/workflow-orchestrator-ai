from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from workflow_ai.connectors.portal_a.config import PortalAConfig
from workflow_ai.connectors.portal_a.selectors import A
from workflow_ai.domain.models import CaseRecord, StepResult
from workflow_ai.ports.browser import BrowserPort


def _digits(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _money_cents(value: str) -> str:
    """Normalize a displayed monetary value to cents for read-back comparison."""
    raw = str(value or "").strip()
    if not raw:
        return ""

    last_comma = raw.rfind(",")
    last_dot = raw.rfind(".")
    separator = max(last_comma, last_dot)

    if separator >= 0:
        integer = re.sub(r"\D", "", raw[:separator]) or "0"
        fraction = re.sub(r"\D", "", raw[separator + 1 :])
        fraction = (fraction + "00")[:2] if fraction else "00"
        normalized = integer + fraction
    else:
        normalized = (re.sub(r"\D", "", raw) or "0") + "00"

    return normalized.lstrip("0") or "0"


def _alnum(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isalnum()).upper()


def _money(value: str, decimals: int) -> str:
    raw = str(value or "").strip()
    if not raw:
        return "0," + ("0" * decimals)
    normalized = raw.replace(" ", "")
    if "," in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")
    try:
        number = float(normalized)
    except ValueError:
        number = 0.0
    text = f"{number:,.{decimals}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


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


@dataclass(slots=True)
class PortalASteps:
    browser: BrowserPort
    config: PortalAConfig

    def in_edit_context(self) -> bool:
        return self.browser.exists(A.PROCESS, timeout=1.0)

    def restore_edit_context(self, record: CaseRecord, external_id: str) -> bool:
        """Safely reopen an existing record only when an explicit edit action exists."""
        if self.in_edit_context():
            return True
        if not external_id or not self.config.search_url:
            return False

        self.browser.navigate(self.config.search_url)
        self.browser.fill(A.SEARCH_PROCESS, record.process_id)
        self.browser.click(A.SEARCH_BUTTON)
        self.browser.page_ready()

        clicked = bool(
            self.browser.execute_script(
                r"""
                const [externalId, processId] = arguments;
                const canon = value => (value || '')
                  .normalize('NFD')
                  .replace(/[\u0300-\u036f]/g, '')
                  .replace(/[^0-9A-Za-z]/g, '')
                  .toUpperCase();

                for (const tr of document.querySelectorAll('#datagrid-0 tbody tr')) {
                  const cells = tr.querySelectorAll('td');
                  if (!cells[1] || !cells[2]) continue;
                  if (canon(cells[1].innerText) !== canon(externalId)) continue;
                  if (canon(cells[2].innerText) !== canon(processId)) continue;

                  const actions = Array.from(
                    tr.querySelectorAll('td.action button, td.action a')
                  );
                  for (const action of actions) {
                    const semantic = [
                      action.innerText,
                      action.getAttribute('title'),
                      action.getAttribute('aria-label')
                    ].filter(Boolean).join(' ').toLowerCase();

                    if (/\b(editar|alterar)\b/i.test(semantic)) {
                      action.click();
                      return true;
                    }
                  }
                }
                return false;
                """,
                external_id,
                record.process_id,
            )
        )
        if not clicked:
            return False

        self.browser.page_ready()
        return self.browser.exists(A.PROCESS, timeout=8.0)

    def prepare(self, record: CaseRecord, external_id: str = "") -> StepResult:
        if external_id:
            if self.restore_edit_context(record, external_id):
                return StepResult(ok=True, message="Contexto existente reaberto com segurança.")
            return StepResult(
                ok=False,
                message=(
                    "Registro existente localizado como retomada, mas não foi possível "
                    "confirmar uma ação explícita de Editar/Alterar. Execução interrompida "
                    "para evitar operar a contratação errada."
                ),
            )

        self.browser.navigate(self.config.create_url)
        return StepResult(ok=True, message="Tela de novo registro aberta.")

    def basic_data(self, record: CaseRecord) -> StepResult:
        required = {
            "process_id": record.process_id,
            "value": record.value,
            "supplier_document": record.supplier_document,
            "supplier_name": record.supplier_name,
            "execution_term": record.execution_term,
            "object_text": record.object_text,
            "act_date": record.act_date,
            "ordering_officer_document": record.ordering_officer_document or record.authority_document,
        }
        missing = [name for name, value in required.items() if not str(value or "").strip()]
        if missing:
            return StepResult(ok=False, message="Campos obrigatórios ausentes: " + ", ".join(missing))

        self.browser.fill(A.PROCESS, record.process_id)
        self.browser.select_value(A.TYPOLOGY, self.config.typology_value)
        self.browser.select_value(A.PRICE_REGISTRATION, self.config.price_registration_value)
        self.browser.fill(A.VALUE, _money(record.value, 2))
        self.browser.select_value(A.ITEM_LOT, self.config.item_lot_value)
        self.browser.select_value(A.LEGAL_BASIS, self.config.legal_basis_value)
        self.browser.fill(A.ORDERING_OFFICER, required["ordering_officer_document"])
        self.browser.fill(A.ACT_DATE, _date_br(record.act_date))
        self.browser.fill(A.SUPPLIER_DOCUMENT, record.supplier_document)
        try:
            actual_name = self.browser.read_value(A.SUPPLIER_NAME, timeout=1.5)
        except Exception:
            actual_name = ""
        if actual_name.strip().casefold() != record.supplier_name.strip().casefold():
            self.browser.fill(A.SUPPLIER_NAME, record.supplier_name)
        self.browser.fill(A.EXECUTION_TERM, record.execution_term)
        self.browser.fill(A.OBJECT, record.object_text)
        self.browser.click(A.SAVE_BASIC)
        self.browser.page_ready()
        self.browser.confirm(("OK", "Confirmar"), timeout=5)
        external_id = ""
        try:
            external_id = self.browser.read_value(A.EXTERNAL_ID, timeout=2)
        except Exception:
            pass
        return StepResult(ok=True, message="Dados básicos gravados.", external_id=external_id)

    def items(self, record: CaseRecord) -> StepResult:
        self.browser.click(A.NEW_ITEM)
        self.browser.fill(A.ITEM_POSITION, record.item_number or "1")
        self.browser.fill(A.ITEM_DESCRIPTION, record.object_text)
        self.browser.fill(A.ITEM_QUANTITY, record.quantity or "1")
        self.browser.select_value(A.ITEM_UNIT, self.config.unit_value)
        self.browser.fill(A.ITEM_UNIT_VALUE, _money(record.value, 4))
        self.browser.click(A.SAVE_MODAL)
        self.browser.confirm(("OK", "Confirmar"), timeout=5)
        self.browser.wait_absent(A.MODAL)
        self.browser.page_ready()
        return StepResult(ok=True, message="Item gravado.")

    def documents(self, record: CaseRecord) -> StepResult:
        path = Path(str(record.file_path or "").strip().strip('"').strip("'")) if record.file_path else None
        if not path:
            if self.config.document_required:
                return StepResult(ok=False, message="Documento obrigatório não informado.")
            return StepResult(ok=True, message="Etapa de documento dispensada.")
        if not path.is_file():
            return StepResult(ok=False, message="Arquivo de documento não encontrado.")
        self.browser.click(A.NEW_DOCUMENT)
        if not self.browser.select_first_containing_option(A.DOCUMENT_MODAL, self.config.document_act_value):
            return StepResult(ok=False, message="Campo de ato não localizado no modal.")
        if not self.browser.select_first_containing_option(A.DOCUMENT_MODAL, self.config.document_type_value):
            return StepResult(ok=False, message="Campo de tipo de documento não localizado no modal.")
        self.browser.upload(A.FILE_INPUT, path)
        self.browser.click(A.SAVE_DOCUMENT)
        self.browser.page_ready()
        self.browser.confirm(("OK", "Confirmar"), timeout=5)
        return StepResult(ok=True, message="Documento gravado.")

    def commitments(self, record: CaseRecord) -> StepResult:
        unit_code = record.commitment_unit_code or self.config.commitment_unit_code
        required = {
            "commitment_year": record.commitment_year,
            "commitment_date": record.commitment_date,
            "commitment_unit_code": unit_code,
            "commitment_number": record.commitment_number,
            "commitment_value": record.commitment_value or record.value,
        }
        missing = [name for name, value in required.items() if not str(value or "").strip()]
        if missing:
            return StepResult(ok=False, message="Dados de empenho ausentes: " + ", ".join(missing))
        self.browser.click(A.NEW_COMMITMENT)
        self.browser.fill(A.COMMITMENT_YEAR, required["commitment_year"])
        self.browser.fill(A.COMMITMENT_DATE, _date_br(required["commitment_date"]))
        self.browser.fill(A.COMMITMENT_UNIT, required["commitment_unit_code"])
        self.browser.fill(A.COMMITMENT_NUMBER, required["commitment_number"])
        self.browser.fill(A.COMMITMENT_VALUE, _money(required["commitment_value"], 2))
        self.browser.click(A.SAVE_COMMITMENT)
        self.browser.confirm(("OK", "Confirmar"), timeout=5)
        self.browser.page_ready()
        return StepResult(ok=True, message="Empenho gravado.")

    def verify(self, record: CaseRecord) -> StepResult:
        errors: list[str] = []
        item = self.browser.last_row_cells(A.ITEM_GRID)
        if not item:
            errors.append("item ausente")
        elif len(item) > 6 and _money_cents(item[6]) != _money_cents(record.value):
            errors.append("valor do item divergente")

        if record.file_path:
            doc = self.browser.last_row_cells(A.DOCUMENT_GRID)
            if not doc:
                errors.append("documento ausente")

        commitment = self.browser.last_row_cells(A.COMMITMENT_GRID)
        if not commitment:
            errors.append("empenho ausente")
        elif len(commitment) > 5:
            if _alnum(commitment[4]) != _alnum(record.commitment_number):
                errors.append("número do empenho divergente")
            if _money_cents(commitment[5]) != _money_cents(
                record.commitment_value or record.value
            ):
                errors.append("valor do empenho divergente")

        if errors:
            return StepResult(ok=False, message="Conferência falhou: " + "; ".join(errors))
        return StepResult(ok=True, message="Conferência pós-gravação aprovada.")

    def submit(self, record: CaseRecord) -> StepResult:
        previous = set(self.browser.window_handles())
        origin = self.browser.current_window()
        self.browser.click(A.SEND)
        self.browser.page_ready()
        if not self.browser.confirm(("Sim", "Confirmar", "OK"), timeout=8):
            return StepResult(ok=False, message="Confirmação do envio não apareceu; estado incerto.")
        self.browser.page_ready()
        self.browser.confirm(("Emitir Recibo", "Emitir", "OK"), timeout=8)
        handles = set(self.browser.window_handles())
        new_handles = handles - previous
        if new_handles:
            self.browser.switch_window(next(iter(new_handles)))
        receipt = self._save_receipt(record)
        if new_handles and origin:
            self.browser.close_window()
            self.browser.switch_window(origin)
        return StepResult(ok=True, message="Envio confirmado.", metadata={"receipt": str(receipt) if receipt else ""})

    def _save_receipt(self, record: CaseRecord) -> Path | None:
        safe_process = re.sub(r'[\\/:*?"<>|\r\n\t]+', "", record.process_id)
        safe_supplier = re.sub(r'[\\/:*?"<>|\r\n\t]+', "", record.supplier_name)[:80]
        destination = self.config.receipt_dir / f"{safe_process}_{safe_supplier}.pdf"
        try:
            return self.browser.print_pdf(destination)
        except Exception:
            return None
