from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.categories_cruds import create_new_category , update_category, delete_category
from app.schemas.category_schema import Category as CategorySchema , CategoryUpdate
from app.db import get_db
from app.core.auth import get_current_admin_user
from app.models import Category as CategoryModel
from sqlalchemy import select

router = APIRouter(
    prefix="/categories",
    tags=['Categories']
)


@router.post("/")
async def create_category(category: CategorySchema, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_admin_user)):
    new_category = await create_new_category(db, category)
    return new_category

@router.get("/")
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CategoryModel))
    categories = result.scalars().all()
    return categories

@router.delete("/delete/{category_id}")
async def delete_category_route(category_id: int, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_admin_user)):
    return await delete_category(db, category_id)

@router.put("/{category_id}")
async def update_category_route(category_id: int, category_update: CategoryUpdate, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_admin_user)):
    updated_category = await update_category(db, category_id, category_update)
    return updated_category



