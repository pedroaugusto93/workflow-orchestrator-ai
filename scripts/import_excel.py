from __future__ import annotations

import argparse
from pathlib import Path

from workflow_ai.application.orchestrator import DuplicateJobError, Orchestrator
from workflow_ai.domain.models import Job, WorkflowKind
from workflow_ai.importers.excel import load_cases, load_records
from workflow_ai.infrastructure.settings import settings
from workflow_ai.infrastructure.sqlite_repo import SQLiteJobRepository


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importa uma planilha local para a fila persistida do orquestrador."
    )
    parser.add_argument("file", type=Path, help="Caminho do arquivo XLSX.")
    parser.add_argument(
        "--workflow",
        required=True,
        choices=[kind.value for kind in WorkflowKind],
        help="Fluxo que receberá os jobs.",
    )
    parser.add_argument("--sheet", default=None, help="Nome da aba. Padrão: aba ativa.")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Permite reprocessamento somente se ALLOW_FORCE_REPROCESS=true.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.file.is_file():
        raise SystemExit(f"Arquivo não encontrado: {args.file}")

    workflow = WorkflowKind(args.workflow)
    if workflow == WorkflowKind.PORTAL_B_PUBLICATION:
        records = load_cases(args.file, args.sheet)
    else:
        records = load_records(args.file, args.sheet)

    repo = SQLiteJobRepository(settings.database_url.removeprefix("sqlite:///"))
    orchestrator = Orchestrator(
        repo,
        {},
        approval_required=settings.approval_required,
        allow_force_reprocess=settings.allow_force_reprocess,
    )

    created = 0
    duplicates = 0
    for record in records:
        try:
            orchestrator.enqueue(
                Job(workflow=workflow, payload=record),
                force=args.force,
            )
            created += 1
            print(f"ENFILEIRADO | {record.process_id}")
        except DuplicateJobError:
            duplicates += 1
            print(f"IGNORADO (job equivalente já existe) | {record.process_id}")

    print(
        f"Resumo: {created} job(s) enfileirado(s), "
        f"{duplicates} duplicado(s) ignorado(s), {len(records)} registro(s)/processo(s) lido(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
