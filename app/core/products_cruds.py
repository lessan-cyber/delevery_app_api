from app.models.product_models import Category, Product, ProductCategory, ProductImage 
from sqlalchemy.orm import Session
from app.schemas import ProductCreate , ProductResponse
from typing import List
from fastapi import HTTPException, status, UploadFile
from app.db.minio import upload_file
from ..config import settings as s

async def create_new_product(db: Session, product_in: ProductCreate):
    # Create the product instance
    product = Product(
        name=product_in.name,
        description=product_in.description,
        price=product_in.price,
        stock=product_in.stock,
        discount=product_in.discount,
        seller_id=product_in.seller_id
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Handle categories
    for category_id in product_in.category_ids:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {category_id} not found")
        product_category = ProductCategory(product_id=product.id, category_id=category_id)
        db.add(product_category)

    # Handle images
    image_urls = []
    if product_in.images:
        if len(product_in.images) > 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A product can have up to 3 images.")
        for image in product_in.images:
            image_url = await upload_file(image, s.minio_bucket, f"products/{image.filename}")
            product_image = ProductImage(product_id=product.id, image_url=image_url)
            db.add(product_image)
            image_urls.append(image_url)

    db.commit()
    db.refresh(product)
    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        discount=product.discount,
        seller_id=product.seller_id,
        image_urls=image_urls)
    

"""from app.models.product_models import Category, Product, ProductCategory, ProductImage
from sqlalchemy.orm import Session
from app.schemas import ProductCreate
from typing import List
from datetime import datetime
from ..db  import upload_file
from ..config import settings as s
from fastapi import HTTPException , status

async def create_new_product(db: Session, product: ProductCreate):
    # check if there is more than 3 image 
    if len(product.images) > 3:
        raise HTTPException(status_code=400, detail="A product cannot have more than 3 images.")

    # handle image uploads and get image URLs
    image_urls = []
    for image in product.images:
        image_urls .append(await upload_file(image, s.minio_bucket, f"products/{image.filename}"))

    # create product
    product_db = Product(
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        image_url=image_urls[0] if image_urls else None,
        discount=product.discount,
        seller_id=product.seller_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(product_db)
    db.commit()
    db.refresh(product_db)

    # add categories
    for category_id in product.category_ids:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {category_id} not found")
        product_category = ProductCategory(product_id=product.id, category_id=category_id)
        db.add(product_category)
    
    # add images
    for image_url in image_urls:
        product_image = ProductImage(image_url=image_url, product_id=product.id)
        db.add(product_image)

    db.commit()
    db.refresh(product_db)
    return product_db"""