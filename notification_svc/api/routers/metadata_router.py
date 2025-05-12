from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from api.schemas.query_schemas import QueryParams, MetadataResponse, FeaturesResponse, PaginatedResponse
from api.services.meta_service import MetadataService
from api.utils.database import get_db

router = APIRouter(prefix="/metadata", tags=["Metadata"])


@router.get("/", response_model=PaginatedResponse)
async def get_meta_list(
    query_params: QueryParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    async with db as session:
        service = MetadataService(session)
        items, total = await service.get_meta_list(query_params)
        
        total_pages = (total + query_params.page_size - 1) // query_params.page_size

        meta_items = [MetadataResponse.model_validate(item) for item in items]
        
        return PaginatedResponse(
            items=meta_items,
            total=total,
            page=query_params.page,
            page_size=query_params.page_size,
            total_pages=total_pages
        )


@router.get("/{meta_id}", response_model=Dict[str, Any])
async def get_meta_with_features(
    meta_id: int,
    db: AsyncSession = Depends(get_db)
):
    async with db as session:
        service = MetadataService(session)
        result = await service.get_meta_with_features(meta_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Meta record not found")
        
        meta, features = result
        return {
            "meta": MetadataResponse.model_validate(meta),
            "features": FeaturesResponse.model_validate(features)
        }


@router.get("/statistics", response_model=Dict[str, Any])
async def get_statistics(
    db: AsyncSession = Depends(get_db)
):
    async with db as session:
        service = MetadataService(session)
        return await service.get_statistics() 