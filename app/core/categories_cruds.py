# FILE: categories_cruds.py

from app.models import Category as CategoryModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.category_schema import Category as CategorySchema , CategoryUpdate
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import select


async def create_new_category(db: AsyncSession, category: CategorySchema):
    new_category = CategoryModel(**category.dict(), created_at=datetime.now())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category


async def update_category(db: AsyncSession, category_id: int, category: CategoryUpdate):
    # Get the existing category
    result = await db.execute(select(CategoryModel).where(CategoryModel.id == category_id))
    existing_category = result.scalar_one_or_none()
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Check if the new category name already exists
    result = await db.execute(select(CategoryModel).where(CategoryModel.name == category.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists",
        )

    if category.name is not None:
        setattr(existing_category, "name", category.name)
    if category.description is not None:
        setattr(existing_category, "description", category.description)
    # updated_at will be set automatically by onupdate=func.now() if configured
    await db.commit()
    await db.refresh(existing_category)
    return existing_category


async def delete_category(db: AsyncSession, category_id: int):
    result = await db.execute(select(CategoryModel).where(CategoryModel.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(category)
    await db.commit()
    return {"message": "Category deleted successfully"}



