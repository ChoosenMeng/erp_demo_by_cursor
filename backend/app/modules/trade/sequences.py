"""Document number sequence helpers."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.trade.models import DocumentSequence

# Default prefixes for MVP doc types
DEFAULT_PREFIX: dict[str, str] = {
    "PO": "PO",
    "SO": "SO",
    "IN": "IN",
    "OUT": "OUT",
    "AP": "AP",
    "AR": "AR",
}


def next_doc_no(db: Session, company_id: int, doc_type: str, actor_id: int | None = None) -> str:
    """Allocate next document number for company+doc_type (row-locked)."""
    row = db.scalar(
        select(DocumentSequence)
        .where(
            DocumentSequence.company_id == company_id,
            DocumentSequence.doc_type == doc_type,
        )
        .with_for_update()
    )
    if row is None:
        row = DocumentSequence(
            company_id=company_id,
            doc_type=doc_type,
            prefix=DEFAULT_PREFIX.get(doc_type, doc_type),
            next_value=1,
            reset_rule="never",
            created_by=actor_id,
            updated_by=actor_id,
        )
        db.add(row)
        db.flush()
        # re-lock
        row = db.scalar(
            select(DocumentSequence)
            .where(DocumentSequence.id == row.id)
            .with_for_update()
        )
        assert row is not None

    value = int(row.next_value)
    row.next_value = value + 1
    row.updated_by = actor_id
    db.flush()
    return f"{row.prefix}{value:06d}"
