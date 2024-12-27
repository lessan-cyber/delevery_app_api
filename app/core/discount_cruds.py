from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.product_models import Discount
from app.schemas.discount_schema import DiscountCreate, DiscountResponse, DiscountUpdate
from app.utils.utils import get_utc_now

async def create_new_discount(db: Session, discount_in: DiscountCreate):
    # Validate dates
    if discount_in.start_date >= discount_in.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )

    current_time = get_utc_now()

    # Check if there's an existing active discount for this product
    existing_discount = db.query(Discount).filter(
        Discount.product_id == discount_in.product_id,
        Discount.end_date > current_time,
        Discount.start_date <= current_time
    ).first()

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
        db.commit()
        db.refresh(new_discount)
        
        return DiscountResponse(
            id=new_discount.id,
            product_id=new_discount.product_id,
            discount_percentage=new_discount.discount_percentage,
            start_date=new_discount.start_date,
            end_date=new_discount.end_date,
            created_at=new_discount.created_at,
            updated_at=new_discount.updated_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

async def update_discount(db: Session, discount_id: int, discount_in: DiscountUpdate):
    discount = db.query(Discount).filter(Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    
    current_time = get_utc_now()
    
    # Check if the discount is active
    if discount.end_date < current_time:
        raise HTTPException(status_code=400, detail="Discount is no longer active")
    
    # Use existing values if not provided in update
    start_date = discount_in.start_date.astimezone(timezone.utc) if discount_in.start_date else discount.start_date
    end_date = discount_in.end_date.astimezone(timezone.utc) if discount_in.end_date else discount.end_date
    
    if end_date <= start_date:
        raise HTTPException(
            status_code=400, 
            detail="End date must be after start date"
        )

    # Update the discount with UTC times
    if discount_in.discount_percentage is not None:
        discount.discount_percentage = discount_in.discount_percentage
    discount.start_date = start_date
    discount.end_date = end_date
    
    db.commit()
    db.refresh(discount)
    return discount

async def delete_discount(db: Session, discount_id: int):
    # check if the discount exists
    discount = db.query(Discount).filter(Discount.id == discount_id).first()
    if not discount:
        raise HTTPException(status_code=404, detail="Discount not found")
    
    # check if the discount is active
    if discount.start_date < get_utc_now() < discount.end_date:
        raise HTTPException(status_code=400, detail="Discount is still active you cannot delete it")
    
    # delete the discount
    db.delete(discount)
    db.commit()
    return {"message": "Discount deleted successfully"}
