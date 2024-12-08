from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.categories_cruds import create_new_category , update_category
from app.schemas.category_schema import Category as CategorySchema , CategoryUpdate
from app.db import get_db
from app.core.auth import get_current_admin_user
from app.models import Category as CategoryModel

router = APIRouter(
    prefix="/categories",
    tags=['Categories']
)


@router.post("/")
async def create_category(category: CategorySchema, db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    new_category = await create_new_category(db, category)
    return new_category

@router.get("/")
async def get_categories(db: Session = Depends(get_db)):
    categories = db.query(CategoryModel).all()
    return categories

@router.delete("/delete/{category_id}")
async def delete_category(category_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    category = db.query(CategoryModel).get(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}

@router.put("/{category_id}")
async def update_category_route(category_id: int, category_update: CategoryUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    updated_category = await update_category(db, category_id, category_update)
    
    return updated_category

