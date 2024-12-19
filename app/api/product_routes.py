from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form, File
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.product_schema import ProductCreate, ProductResponse
from app.db import get_db
from app.core.auth import get_current_user
from app.core.products_cruds import create_new_product
from app.models.user_models import CompanyProfile, User

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product_route(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    price: float = Form(...),
    stock: int = Form(...),
    discount: Optional[float] = Form(None),
    category_ids: List[int] = Form(...),
    images: List[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    currency: str = Form(...)

):
    # Check if user is a seller
    company_profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == current_user.id).first()
    if not company_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="You are not allowed to create a product, only companies can create products")

    # Ensure images is a list
    if images is None:
        images = []
    elif not isinstance(images, list):
        images = [images]

    product_in = ProductCreate(
        name=name,
        description=description,
        price=price,
        stock=stock,
        discount=discount,
        category_ids=category_ids,
        images=images,
        seller_id=current_user.id ,
        currency = currency
    )

    try:
        new_product =await  create_new_product(db, product_in)
        return new_product
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))