from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.product_models import Discount
from app.schemas.discount_schema import DiscountCreate, DiscountResponse, DiscountUpdate
from app.utils.utils import get_utc_now

async def create_new_discount(db: AsyncSession, discount_in: DiscountCreate):
    """Create a new discount for a product asynchronously.

    Args:
        db (AsyncSession): The async database session.
        discount_in (DiscountCreate): Discount creation data.

    Returns:
        DiscountResponse: The created discount response.

    Raises:
        HTTPException: If validation fails or DB error occurs.
    """
    # Validate dates
    if discount_in.start_date >= discount_in.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )

    current_time = get_utc_now()

    # Check if there's an existing active discount for this product
    result = await db.execute(
        select(Discount).where(
            Discount.product_id == discount_in.product_id,
            Discount.end_date > current_time,
            Discount.start_date <= current_time
        )
    )
    existing_discount = result.scalar_one_or_none()

    if existing_discount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already an active discount for this product"
        )

    # Create new discount with UTC times
    new_discount = Discount(
        product_id=discount_in.product_id,
        discount_percentage=discount_in.discount_percentage,
        start_date=discount_in.start_date.astimezone(timezone.utc),
        end_date=discount_in.end_date.astimezone(timezone.utc)
    )

    try:
        db.add(new_discount)
        await db.commit()
        await db.refresh(new_discount)
        return DiscountResponse.from_orm(new_discount)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

async def update_discount(db: AsyncSession, discount_id: int, discount_in: DiscountUpdate):
    """Update an existing discount asynchronously.

    Args:
        db (AsyncSession): The async database session.
        discount_id (int): The discount ID to update.
        discount_in (DiscountUpdate): Discount update data.

    Returns:
        DiscountResponse: The updated discount response.

    Raises:
        HTTPException: If not found, validation fails, or DB error occurs.
    """
    result = await db.execute(select(Discount).where(Discount.id == discount_id))
    discount = result.scalar_one_or_none()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")

    current_time = get_utc_now()

    # Check if the discount is active
    end_date_val = getattr(discount, "end_date", None)
    if isinstance(end_date_val, datetime) and current_time is not None and end_date_val < current_time:
        raise HTTPException(status_code=400, detail="Discount is no longer active")

    # Use existing values if not provided in update
    start_date = discount_in.start_date.astimezone(timezone.utc) if discount_in.start_date else discount.start_date
    end_date = discount_in.end_date.astimezone(timezone.utc) if discount_in.end_date else discount.end_date

    if isinstance(end_date, datetime) and isinstance(start_date, datetime) and end_date <= start_date:
        raise HTTPException(
            status_code=400,
            detail="End date must be after start date"
        )

    # Update the discount with UTC times
    if discount_in.discount_percentage is not None:
        setattr(discount, "discount_percentage", discount_in.discount_percentage)
    setattr(discount, "start_date", start_date)
    setattr(discount, "end_date", end_date)

    await db.commit()
    await db.refresh(discount)
    return DiscountResponse.from_orm(discount)

async def delete_discount(db: AsyncSession, discount_id: int):
    """Delete a discount asynchronously.

    Args:
        db (AsyncSession): The async database session.
        discount_id (int): The discount ID to delete.

    Returns:
        dict: Success message.

    Raises:
        HTTPException: If not found, still active, or DB error occurs.
    """
    result = await db.execute(select(Discount).where(Discount.id == discount_id))
    discount = result.scalar_one_or_none()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")

    # check if the discount is active
    now = get_utc_now()
    start_date_val = getattr(discount, "start_date", None)
    end_date_val = getattr(discount, "end_date", None)
    if (
        isinstance(start_date_val, datetime)
        and isinstance(end_date_val, datetime)
        and start_date_val < now < end_date_val
    ):
        raise HTTPException(status_code=400, detail="Discount is still active you cannot delete it")

    await db.delete(discount)
    await db.commit()
    return {"message": "Discount deleted successfully"}
