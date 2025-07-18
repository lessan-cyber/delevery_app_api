from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new discount for a product.

    Args:
        discount_in (DiscountCreate): Discount creation data.
        db (AsyncSession): Async database session.
        current_user (User): The current authenticated user.

    Returns:
        DiscountResponse: The created discount response.
    """
    # First check if product exists
    result = await db.execute(select(Product).where(Product.id == discount_in.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {discount_in.product_id} not found"
        )

    # Then check if user owns the product
    seller_id_val = getattr(product, "seller_id", None)
    if seller_id_val is None or seller_id_val != current_user.id:
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing discount for a product.

    Args:
        discount_id (int): The discount ID to update.
        discount_in (DiscountUpdate): Discount update data.
        db (AsyncSession): Async database session.
        current_user (User): The current authenticated user.

    Returns:
        DiscountResponse: The updated discount response.
    """
    # First check if product exists
    result = await db.execute(select(Product).where(Product.id == discount_in.product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {discount_in.product_id} not found"
        )
    # Then check if user owns the product
    seller_id_val = getattr(product, "seller_id", None)
    if seller_id_val is None or seller_id_val != current_user.id:
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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a discount for a product.

    Args:
        discount_id (int): The discount ID to delete.
        db (AsyncSession): Async database session.
        current_user (User): The current authenticated user.

    Returns:
        dict: Success message.
    """
    from sqlalchemy.orm import selectinload
    # Eagerly load the discount with its product relationship
    result = await db.execute(
        select(Discount).options(selectinload(Discount.product)).where(Discount.id == discount_id)
    )
    discount = result.scalar_one_or_none()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    # check if the user owns the product
    product_obj = discount.product
    seller_id_val = getattr(product_obj, "seller_id", None) if product_obj else None
    if seller_id_val is None or seller_id_val != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own discounts")
    # Now call the CRUD to delete the discount (do not access relationships after this)
    return await delete_discount_crud(db, discount_id)