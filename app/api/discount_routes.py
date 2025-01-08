from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.core.auth import get_current_user
from app.models.user_models import User
from app.models.product_models import Product, Discount
from app.schemas.discount_schema import DiscountCreate, DiscountResponse, DiscountUpdate
from app.core.discount_cruds import create_new_discount, update_discount as update_discount_crud, delete_discount as delete_discount_crud   

router = APIRouter(
    prefix="/discounts",
    tags=["Discounts"]
)

@router.post("/", response_model=DiscountResponse)
async def create_discount(
    discount_in: DiscountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # First check if product exists
    product = db.query(Product).filter(Product.id == discount_in.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {discount_in.product_id} not found"
        )

    # Then check if user owns the product
    if product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create discounts for your own products"
        )

    try:
        new_discount = await create_new_discount(db, discount_in)
        return new_discount
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{discount_id}", response_model=DiscountResponse)
async def update_discount(
    discount_id: int,
    discount_in: DiscountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):      
    # First check if product exists
    product = db.query(Product).filter(Product.id == discount_in.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {discount_in.product_id} not found"
        )
    # Then check if user owns the product
    if product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only create discounts for your own products"
        )
    try:
        updated_discount = await update_discount_crud(db, discount_id, discount_in)
        return updated_discount
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.delete("/{discount_id}")
async def delete_discount(
    discount_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # check if the discount exists
    discount = db.query(Discount).filter(Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    # check if the user owns the product
    if discount.product.seller_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own discounts")
    return await delete_discount_crud(db, discount_id)