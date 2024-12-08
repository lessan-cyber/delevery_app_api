from pydantic import BaseModel , HttpUrl
from typing import List, Optional
from .category_schema import Category
from fastapi import UploadFile

# Modèle de base
""" class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    discount: Optional[float] = None

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
    category_ids: List[int]  # Liste des IDs des catégories associées
    images: Optional[List[UploadFile]] = None  # List of image files (up to 3)

    @classmethod
    def validate_images(cls, images: Optional[List[UploadFile]]):
        if images and len(images) > 3:
            raise ValueError("A product can have up to 3 images.")
        return images

    class Config:

        from_attributes = True
    

"""



class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    discount: Optional[float] = None

class ProductImageCreate(BaseModel):
    id: int
    image: UploadFile

    class Config:
        orm_mode = True

class ProductImage(BaseModel):
    id: int
    image_url: str

    class Config:
        orm_mode = True

class ProductCreate(ProductBase):
    category_ids: List[int]  # Liste des IDs des catégories associées
    images: Optional[List[UploadFile]] = None  # List of image files (up to 3)
    seller_id: int

    @classmethod
    def validate_images(cls, images: Optional[List[UploadFile]]):
        if images and len(images) > 3:
            raise ValueError("A product can have up to 3 images.")
        return images

    class Config:
        orm_mode = True

class ProductResponse(ProductBase):
    id: int
    categories: List[Category] = []
    images: List[ProductImage] = []

    class Config:
        from_attributes = True
        
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    category_ids: Optional[List[int]] = None
    images: Optional[List[HttpUrl]] = None  # List of image URLs (up to 3)
    discount: Optional[float] = None

    @classmethod
    def validate_images(cls, images: Optional[List[HttpUrl]]):
        if images and len(images) > 3:
            raise ValueError("A product can have up to 3 images.")
        return images

    class Config:
          from_attributes = True