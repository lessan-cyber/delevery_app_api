from app.models.product_models import Category, Product, ProductCategory, ProductImage , Discount
from app.schemas.product_schema import ProductWithDiscount
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import ProductCreate , ProductResponse , ProductImage as ProductImageSchema, ProductUpdate
from typing import List
from fastapi import HTTPException, status
from app.db.minio import upload_file, delete_file
from ..config import settings as s
from ..utils import log
from app.utils.utils import get_utc_now 
from app.utils.currency_exchange import supported_currencies as list_of_supported_currencies
from sqlalchemy import select
from app.schemas.category_schema import Category as CategorySchema
from sqlalchemy.orm import selectinload
from decimal import Decimal
async def create_new_product(db: AsyncSession, product_in: ProductCreate):
    # Create the product instance
    product = Product(
        name=product_in.name,
        description=product_in.description,
        price=product_in.price,
        stock=product_in.stock,
        seller_id=product_in.seller_id ,
        currency = product_in.currency
    )
    # check if the currency is supported
   
    if isinstance(product_in.currency, str) and product_in.currency not in list_of_supported_currencies:
        raise HTTPException(status_code=400, detail="The currency is not supported")
    db.add(product)
    await db.commit()
    await db.refresh(product)

    # Eagerly load relationships to avoid MissingGreenlet errors
    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.images),
            selectinload(Product.product_categories).selectinload(ProductCategory.category)
        )
        .where(Product.id == product.id)
    )
    product = result.scalar_one_or_none()

    # Handle categories
    categories = []
    for pc in getattr(product, 'product_categories', []):
        if pc.category:
            categories.append(CategorySchema.from_orm(pc.category))

    # Handle images
    image_urls = []
    for img in getattr(product, 'images', []):
        image_urls.append(ProductImageSchema.from_orm(img))

    # Prepare the response
    return ProductResponse(
        id=getattr(product, 'id', 0),
        name=getattr(product, 'name', ''),
        description=getattr(product, 'description', ''),
        price=Decimal(getattr(product, 'price', 0)),
        stock=getattr(product, 'stock', 0),
        currency=getattr(product, 'currency', ''),
        categories=categories,
        images=image_urls,
    )



async def updateProduct(db: AsyncSession, product_id: int, product_update: ProductUpdate, user_id: int):
    # Get the existing product with relationships
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user owns the product
    if isinstance(product.seller_id, int) and product.seller_id != user_id:
        raise HTTPException(
            status_code=403, 
            detail="You are not allowed to update this product"
        )

    # Update product fields if provided
    if product_update.name is not None:
        setattr(product, 'name', product_update.name)
    if product_update.description is not None:
        setattr(product, 'description', product_update.description)
    if product_update.price is not None:
        setattr(product, 'price', product_update.price)
    if product_update.stock is not None:
        setattr(product, 'stock', product_update.stock)
    if product_update.currency is not None:
        # Check if the currency is supported
        if isinstance(product_update.currency, str) and product_update.currency not in list_of_supported_currencies:
            raise HTTPException(status_code=400, detail="The currency is not supported")
        setattr(product, 'currency', product_update.currency)

    # Handle categories if provided
    if product_update.category_ids is not None and len(product_update.category_ids) > 0:
        # Get existing categories
        result = await db.execute(select(ProductCategory).where(ProductCategory.product_id == product.id))
        existing_categories = result.scalars().all()
        existing_category_ids = {pc.category_id for pc in existing_categories}

        # Add new categories
        for category_id in product_update.category_ids:
            if category_id not in existing_category_ids:
                result = await db.execute(select(Category).where(Category.id == category_id))
                category = result.scalar_one_or_none()
                if not category:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"Category with id {category_id} not found"
                    )
                new_category = ProductCategory(
                    product_id=product.id, 
                    category_id=category_id
                )
                db.add(new_category)

    # Handle images if provided
    if product_update.images is not None and len(product_update.images) > 0:
        # Get existing images count
        result = await db.execute(select(ProductImage).where(ProductImage.product_id == product.id))
        existing_images = result.scalars().all()
        
        # Check total images limit
        if len(existing_images) + len(product_update.images) > 3:
            raise HTTPException(
                status_code=400, 
                detail="A product can have up to 3 images"
            )

        # Upload new images
        for image in product_update.images:
            image_url = await upload_file(
                image, 
                s.minio_bucket or "default-bucket", 
                f"products/{image.filename}"
            )
            new_image = ProductImage(
                product_id=product.id, 
                image_url=image_url
            )
            db.add(new_image)

    # Commit changes
    await db.commit()
    await db.refresh(product)

    # Eagerly load relationships to avoid MissingGreenlet errors
    result = await db.execute(
        select(Product)
        .options(
            selectinload(Product.images),
            selectinload(Product.product_categories).selectinload(ProductCategory.category)
        )
        .where(Product.id == product.id)
    )
    product = result.scalar_one_or_none()

    # Get updated categories and images
    categories = []
    for pc in getattr(product, 'product_categories', []):
        if pc.category:
            categories.append(CategorySchema.from_orm(pc.category))

    images = []
    for img in getattr(product, 'images', []):
        images.append(ProductImageSchema.from_orm(img))

    return ProductResponse(
        id=getattr(product, 'id', 0),
        name=getattr(product, 'name', ''),
        description=getattr(product, 'description', ''),
        price=Decimal(getattr(product, 'price', 0)),
        stock=getattr(product, 'stock', 0),
        currency=getattr(product, 'currency', ''),
        categories=categories,
        images=images,
    )



async def delete_product(db: AsyncSession, product_id: int, user_id: int):
    # check if the product exists, eagerly load images
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.images))
        .where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # check if it is the seller who is deleting the product
    if isinstance(product.seller_id, int) and product.seller_id != user_id:
        raise HTTPException(status_code=403, detail="You are not allowed to delete this product")
    # delete the product images
    for image in product.images:
        # get image unique name by removing the url
        image_unique_name = image.image_url.split("/")[-1]
        log.info(f"Deleting image {image_unique_name} from {s.minio_bucket or 'default-bucket'}")
        await delete_file(s.minio_bucket or "default-bucket", image_unique_name)
    # delete product categories
    await db.execute(ProductCategory.__table__.delete().where(ProductCategory.product_id == product.id))
    await db.commit()
    # delete the product
    await db.delete(product)
    await db.commit()
    return {"message": "Product deleted successfully"}


# get a product with its discounts
async def get_product_with_discounts(db: AsyncSession, product_id: int):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # check if the product has an active discount
    current_time = get_utc_now()
    result = await db.execute(
        select(Discount).where(
            Discount.product_id == product.id,
            Discount.start_date <= current_time,
            Discount.end_date > current_time
        )
    )
    discount = result.scalar_one_or_none()

    # Use the new helper method to create the response
    return ProductWithDiscount.from_orm_with_discount(product, discount)

