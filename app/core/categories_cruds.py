# FILE: categories_cruds.py

from app.models import Category as CategoryModel
from sqlalchemy.orm import Session
from app.schemas.category_schema import Category as CategorySchema , CategoryUpdate
from datetime import datetime
from fastapi import HTTPException, status


async def create_new_category(db: Session, category: CategorySchema):
    new_category = CategoryModel(**category.dict(), created_at=datetime.now())
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


async def update_category(db: Session, category_id: int, category: CategoryUpdate):
    existing_category = (
        db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
    )
    if not existing_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    # Check if the new category name already exists
    if db.query(CategoryModel).filter(CategoryModel.name == category.name).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists",
        )

    existing_category.name = category.name
    existing_category.description = category.description
    existing_category.updated_at = datetime.now()
    db.commit()
    db.refresh(existing_category)
    return existing_category


async def delete_category(db: Session, category_id: int):
    category = db.query(CategoryModel).get(category_id)
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}



