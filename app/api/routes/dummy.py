from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_permission
from app.models import User

router = APIRouter(prefix="/dummy", tags=["dummy"])


@router.get("/reports/finance")
async def finance_report(_: User = Depends(require_permission("reports:finance"))):
    return {"report": "Finance numbers for the month", "status": "ok"}


@router.get("/reports/operations")
async def operations_report(_: User = Depends(require_permission("reports:operations"))):
    return {"report": "Operations metrics", "status": "ok"}


@router.get("/support/tickets")
async def view_tickets(_: User = Depends(require_permission("support:tickets:view"))):
    return {"tickets": [{"id": 1, "subject": "Printer down"}]}


@router.post("/support/tickets")
async def create_ticket(_: User = Depends(require_permission("support:tickets:create"))):
    return {"message": "Ticket created", "ticket_id": 42}
