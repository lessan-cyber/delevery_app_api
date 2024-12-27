from pydantic import BaseModel
from typing import List, Optional
from .category_schema import Category
from .discount_schema import DiscountResponse
from fastapi import UploadFile
from decimal import Decimal

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: Decimal
    stock: int
    currency: str

class ProductImageCreate(BaseModel):
    id: int
    image: UploadFile

    class Config:
        from_attributes = True

class ProductImage(BaseModel):
    id: int
    image_url: str

    class Config:
        from_attributes = True

class ProductCreate(ProductBase):
    category_ids: List[int]
    images: Optional[List[UploadFile]] = None
    seller_id: int

    class Config:
        from_attributes = True

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    category_ids: Optional[List[int]] = None
    images: Optional[List[UploadFile]] = None
    currency: Optional[str] = None

    class Config:
        from_attributes = True

class ProductResponse(ProductBase):
    id: int
    categories: List[Category] = []
    images: List[ProductImage] = []

    class Config:
        from_attributes = True

class ProductWithDiscount(ProductResponse):
    discount: Optional[DiscountResponse] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_discount(cls, product, discount=None):
        return cls(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            stock=product.stock,
            currency=product.currency,
            categories=[Category(id=pc.category.id, name=pc.category.name) 
                       for pc in product.product_categories],
            images=[ProductImage(id=img.id, image_url=img.image_url) 
                   for img in product.images],
            discount=DiscountResponse.from_orm(discount) if discount else None
        )
