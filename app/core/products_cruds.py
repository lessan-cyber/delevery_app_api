from app.models.product_models import Category, Product, ProductCategory, ProductImage 
from sqlalchemy.orm import Session
from app.schemas import ProductCreate , ProductResponse , ProductImage as ProductImageSchema
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
        seller_id=product_in.seller_id ,
        currency = product_in.currency
    )
    # check if the currency is supported
    list_of_supported_currencies = ["Us Dollar" , "Franc CFA", "Euro" , "Naira" , "Rouble"  ,"Yuan", "Yen"  , "Pound Sterling" , "Rand" , "Rupee" , "Real" , "Peso" , "Dinar" , "Dirham" , "Krone" , "Krona" , "Forint" , "Kuna" , "Koruna" , "Lira" , "Leu" , "Lek" , "Lira" , "Marka" , "Pataca" , "Peso" , "Pula" , "Rial" , "Riyal" , "Rufiyaa" , "Rupiah" , "Shekel" , "Taka" , "Tenge" , "Tugrik" , "Won" , "Zloty" , "Baht"]
    if product_in.currency not in list_of_supported_currencies:
        raise HTTPException(status_code=400, detail="The currency is not supported")
    db.add(product)
    db.commit()
    db.refresh(product)

    # Handle categories
    categories = []
    for category_id in product_in.category_ids:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {category_id} not found")
        product_category = ProductCategory(product_id=product.id, category_id=category_id)
        db.add(product_category)
        categories.append(Category(id=category.id , name=category.name))

    # Handle images
    image_urls = []
    if product_in.images:
        if len(product_in.images) > 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A product can have up to 3 images.")
        for image in product_in.images:
            image_url = await upload_file(image, s.minio_bucket, f"products/{image.filename}")
            product_image = ProductImage(product_id=product.id, image_url=image_url)
            db.add(product_image)
            db.commit()
            db.refresh(product_image)
            image_urls.append(ProductImageSchema(id=product_image.id, image_url=image_url))


    db.commit()
    db.refresh(product)
    # Prepare the response
    product_response = ProductResponse(
        id=product.id ,
        name=product.name ,
        description=product.description ,
        price=product.price ,
        stock=product.stock ,
        discount=product.discount ,
        categories=categories ,
        images=image_urls ,
        currency = product.currency ,
    )
    return product_response
