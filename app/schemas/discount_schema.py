from pydantic import BaseModel, validator
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import dateutil.parser
from dateutil.parser import ParserError

class DiscountBase(BaseModel):
    product_id: int
    discount_percentage: Decimal
    start_date: datetime
    end_date: datetime

    @validator('start_date', 'end_date', pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                # First validate the format roughly
                if 'T' in v:
                    # If it's ISO format, validate the parts
                    date_part, time_part = v.split('T')
                    if 'Z' in time_part:
                        time_part = time_part.replace('Z', '+00:00')
                    
                    # Extract hours from time part
                    hours = int(time_part.split(':')[0])
                    if hours >= 24:
                        raise ValueError("Hours must be between 0 and 23")

                # Use dateutil parser for final parsing
                dt = dateutil.parser.parse(v)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except (ValueError, ParserError) as e:
                raise ValueError(f"Invalid datetime format: {str(e)}")
        elif isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        raise ValueError("Value must be a string or datetime object")

    @validator('discount_percentage')
    def validate_discount_percentage(cls, v):
        if not 0 < v <= 100:
            raise ValueError('Discount percentage must be between 0 and 100')
        return v

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

class DiscountCreate(DiscountBase):
    pass

class DiscountUpdate(BaseModel):
    discount_percentage: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    product_id: int

    @validator('start_date', 'end_date', pre=True)
    def parse_datetime(cls, v):
        if v is not None:
            if isinstance(v, str):
                try:
                    # First validate the format roughly
                    if 'T' in v:
                        # If it's ISO format, validate the parts
                        date_part, time_part = v.split('T')
                        if 'Z' in time_part:
                            time_part = time_part.replace('Z', '+00:00')
                        
                        # Extract hours from time part
                        hours = int(time_part.split(':')[0])
                        if hours >= 24:
                            raise ValueError("Hours must be between 0 and 23")

                    # Use dateutil parser for final parsing
                    dt = dateutil.parser.parse(v)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except (ValueError, ParserError) as e:
                    raise ValueError(f"Invalid datetime format: {str(e)}")
            elif isinstance(v, datetime):
                if v.tzinfo is None:
                    return v.replace(tzinfo=timezone.utc)
                return v
        return v

class DiscountResponse(DiscountBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @validator('created_at', 'updated_at', 'start_date', 'end_date', pre=True)
    def ensure_timezone(cls, v):
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        return v

    @classmethod
    def from_orm(cls, db_discount):
        if db_discount is None:
            return None
        return cls(
            id=db_discount.id,
            product_id=db_discount.product_id,
            discount_percentage=db_discount.discount_percentage,
            start_date=db_discount.start_date,
            end_date=db_discount.end_date,
            created_at=db_discount.created_at,
            updated_at=db_discount.updated_at
        )

