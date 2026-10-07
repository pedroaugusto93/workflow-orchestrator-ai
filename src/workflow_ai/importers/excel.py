from __future__ import annotations

from collections import defaultdict
from dataclasses import fields
from pathlib import Path
from typing import Iterable

from openpyxl import load_workbook

from workflow_ai.domain.models import CaseRecord, ContractLineItem


ALIASES = {
    "PROCESSO": "process_id",
    "NOME_CURSO": "title",
    "OBJETO": "object_text",
    "CNPJ_CPF_FORNECEDOR": "supplier_document",
    "CNPJ_FORNECEDOR": "supplier_document",
    "NOME_FORNECEDOR": "supplier_name",
    "VALOR": "value",
    "VALOR_UNIT": "value",
    "PRAZO_EXECUCAO": "execution_term",
    "DATA_INICIO": "start_date",
    "DATA_EMPENHO": "commitment_date",
    "ANO_EMPENHO": "commitment_year",
    "COD_UG_SIAFE": "commitment_unit_code",
    "NUM_ITEM": "item_number",
    "item": "item_number",
    "QTD_ITEM": "quantity",
    "CPF_ORDENADOR": "ordering_officer_document",
    "NUM_EMPENHO": "commitment_number",
    "VALOR_EMPENHO": "commitment_value",
    "processoLink": "source_link",
    "file_path": "file_path",
    "resp_cpf": "responsible_document",
    "resp_email": "responsible_email",
    "autoridade_nome": "authority_name",
    "autoridade_cpf": "authority_document",
    "autoridade_email": "authority_email",
    "data_ato": "act_date",
    "ordenador": "ordering_officer",
}

_PROCESS_FIELDS = {
    "title", "object_text", "execution_term", "start_date", "commitment_date",
    "commitment_year", "commitment_unit_code", "source_link", "file_path",
    "responsible_document", "responsible_email", "authority_name",
    "authority_document", "authority_email", "act_date", "ordering_officer",
    "ordering_officer_document",
}


def load_records(path: str | Path, sheet_name: str | None = None) -> list[CaseRecord]:
    raw_rows = _load_rows(path, sheet_name)
    records: list[CaseRecord] = []
    for raw in raw_rows:
        known, extras = _map_row(raw)
        if not known.get("process_id"):
            continue
        known["extras"] = extras
        records.append(CaseRecord(**known))
    return records


def load_cases(path: str | Path, sheet_name: str | None = None) -> list[CaseRecord]:
    return consolidate_by_process(load_records(path, sheet_name))


def consolidate_by_process(records: Iterable[CaseRecord]) -> list[CaseRecord]:
    grouped = group_by_process(records)
    cases: list[CaseRecord] = []
    for process_id, rows in grouped.items():
        first = rows[0]
        process_values: dict[str, object] = {"process_id": process_id}
        for field_name in _PROCESS_FIELDS:
            values = _unique_nonempty(str(getattr(row, field_name, "") or "").strip() for row in rows)
            if len(values) > 1:
                raise ValueError(
                    f"Processo {process_id}: valores conflitantes em {field_name}: "
                    + " | ".join(values)
                )
            process_values[field_name] = values[0] if values else ""

        items = [
            ContractLineItem(
                item_number=row.item_number,
                title=row.title,
                description=row.object_text,
                supplier_document=row.supplier_document,
                supplier_name=row.supplier_name,
                value=row.value,
                unit_value=row.value,
                quantity=row.quantity or "1",
                alias=row.supplier_name or row.item_number,
                extras=dict(row.extras),
            )
            for row in rows
        ]
        process_values.update(
            supplier_document=first.supplier_document,
            supplier_name=first.supplier_name,
            value=first.value,
            commitment_number=first.commitment_number,
            commitment_value=first.commitment_value,
            item_number=first.item_number,
            quantity=first.quantity,
            items=items,
            extras={"row_count": len(rows)},
        )
        cases.append(CaseRecord(**process_values))
    return cases


def group_by_process(records: Iterable[CaseRecord]) -> dict[str, list[CaseRecord]]:
    grouped: dict[str, list[CaseRecord]] = defaultdict(list)
    for record in records:
        grouped[record.process_id].append(record)
    return dict(grouped)


def _load_rows(path: str | Path, sheet_name: str | None) -> list[dict[str, object]]:
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb[sheet_name] if sheet_name and sheet_name in wb.sheetnames else wb.active
        rows = ws.iter_rows(values_only=True)
        headers = [str(v or "").strip() for v in next(rows)]
        return [dict(zip(headers, values)) for values in rows]
    finally:
        wb.close()


def _map_row(raw: dict[str, object]) -> tuple[dict[str, str], dict[str, object]]:
    known_fields = {f.name for f in fields(CaseRecord)}
    known: dict[str, str] = {}
    extras: dict[str, object] = {}
    for key, value in raw.items():
        if not key:
            continue
        target = ALIASES.get(key)
        if target and target in known_fields:
            known[target] = str(value or "").strip()
        else:
            extras[key] = value
    return known, extras


def _unique_nonempty(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
