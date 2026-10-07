from fastapi import APIRouter, status

from app.api.deps import CurrentUser

from .deps import MemoryServiceDep
from .schemas import MemoryFactRead

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/facts")
def list_memory_facts(user: CurrentUser, service: MemoryServiceDep) -> list[MemoryFactRead]:
    return service.list_facts(user.id)


@router.delete("/facts/{fact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory_fact(fact_id: int, user: CurrentUser, service: MemoryServiceDep) -> None:
    service.delete_fact(user.id, fact_id)
