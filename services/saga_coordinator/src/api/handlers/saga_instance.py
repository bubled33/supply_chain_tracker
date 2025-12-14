from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from src.api.deps.getters import get_saga_service
from src.api.dto.saga_instance import SagaDTO, SagaCreateDTO, SagaUpdateDTO
from src.api.mappers.saga_instance import SagaMapper
from src.app.services.saga_instance import SagaService

saga_router = APIRouter(prefix="/saga_instances", tags=["SAGA"])


@saga_router.post(
    "",
    response_model=SagaDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_saga(
        dto: SagaCreateDTO,
        service: SagaService = Depends(get_saga_service),
):
    """
    Ручное создание новой саги (обычно для тестирования или администрирования).
    В штатном режиме саги создаются через события.
    """
    saga_instance = SagaMapper.create_dto_to_entity(dto)

    created = await service.create(saga_instance)

    return SagaMapper.entity_to_dto(created)


@saga_router.get(
    "/{saga_id}",
    response_model=SagaDTO,
)
async def get_saga(
        saga_id: UUID,
        service: SagaService = Depends(get_saga_service),
):
    """Получить информацию о саге по ID"""
    saga_instance = await service.get(saga_id)
    if saga_instance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saga {saga_id} not found"
        )
    return SagaMapper.entity_to_dto(saga_instance)


@saga_router.get(
    "/by-shipment/{shipment_id}",
    response_model=SagaDTO,
)
async def get_saga_by_shipment(
        shipment_id: UUID,
        service: SagaService = Depends(get_saga_service),
):
    """Получить активную сагу для конкретного отправления"""
    saga_instance = await service.get_by_shipment(shipment_id)
    if saga_instance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active saga for shipment {shipment_id} not found"
        )
    return SagaMapper.entity_to_dto(saga_instance)


@saga_router.get(
    "",
    response_model=List[SagaDTO],
)
async def list_active_sagas(
        service: SagaService = Depends(get_saga_service),
):
    """
    Получить список всех активных (незавершенных) саг.
    Полезно для мониторинга зависших процессов.
    """
    saga_instances = await service.list_active_sagas()
    return [SagaMapper.entity_to_dto(s) for s in saga_instances]


@saga_router.patch(
    "/{saga_id}",
    response_model=SagaDTO,
)
async def update_saga_context(
        saga_id: UUID,
        dto: SagaUpdateDTO,
        service: SagaService = Depends(get_saga_service),
):
    """
    Обновить контекст саги или форсировать изменение статуса (Admin API).
    """
    saga_instance = await service.get(saga_id)
    if saga_instance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saga {saga_id} not found"
        )

    updated_entity = SagaMapper.update_entity_from_dto(saga_instance, dto)
    saved = await service.update_context(
        saga_id=saga_instance.saga_id,
        warehouse_id=updated_entity.warehouse_id,
        delivery_id=updated_entity.delivery_id
    )

    return SagaMapper.entity_to_dto(saved)
