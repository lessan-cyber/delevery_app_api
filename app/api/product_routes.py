from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, Form, File , Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.schemas.product_schema import ProductCreate, ProductResponse, ProductUpdate, ProductWithDiscount
from app.db import get_db
from app.core.auth import get_current_user
from app.core.products_cruds import create_new_product, updateProduct , delete_product , get_product_with_discounts as get_product_with_discounts_crud
from app.models.user_models import CompanyProfile, User
import json

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
    
    
@router.put("/{product_id}", response_model=ProductResponse)
async def update_product_route(
    
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    category_ids: str = Form(None),
    images: List[UploadFile] = File(None),
    currency: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check if user is a seller
    company_profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == current_user.id).first()
    if not company_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only companies can update products"
        )

    # Parse category_ids from JSON string if provided
    parsed_category_ids = None
    if category_ids:
        try:
            parsed_category_ids = json.loads(category_ids)
            if not isinstance(parsed_category_ids, list):
                raise HTTPException(
                    status_code=400,
                    detail="category_ids must be a JSON array"
                )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid JSON format for category_ids"
            )

    # Ensure images is a list
    if images is not None:
        if not isinstance(images, list):
            images = [images]

    product_update = ProductUpdate(
        name=name,
        description=description,
        price=price,
        stock=stock,
        category_ids=parsed_category_ids,
        images=images,
        currency=currency
    )

    try:
        updated_product = await updateProduct(db, product_id, product_update, current_user.id)
        return updated_product
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )
    

@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product_route(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await delete_product(db, product_id, current_user.id)
    return {"message": "Product deleted successfully"}


@router.get("/{product_id}", response_model=ProductWithDiscount)
async def get_product_with_discounts(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db)
):
    print(request.client.host)
    return await get_product_with_discounts_crud(db, product_id)