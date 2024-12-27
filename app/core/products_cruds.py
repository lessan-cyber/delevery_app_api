from app.models.product_models import Category, Product, ProductCategory, ProductImage , Discount
from app.schemas.product_schema import ProductWithDiscount
from sqlalchemy.orm import Session
from app.schemas import ProductCreate , ProductResponse , ProductImage as ProductImageSchema, ProductUpdate
from typing import List
from fastapi import HTTPException, status
from app.db.minio import upload_file, delete_file
from ..config import settings as s
from ..utils import log
from app.utils.utils import get_utc_now
async def create_new_product(db: Session, product_in: ProductCreate):
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
        if len(product_in.images) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You must upload at least one image")
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
        categories=categories ,
        images=image_urls ,
        currency = product.currency ,
    )
    return product_response



async def updateProduct(db: Session, product_id: int, product_update: ProductUpdate, user_id: int):
    # Get the existing product with relationships
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user owns the product
    if product.seller_id != user_id:
        raise HTTPException(
            status_code=403, 
            detail="You are not allowed to update this product"
        )

    # Update product fields if provided
    if product_update.name is not None:
        product.name = product_update.name
    if product_update.description is not None:
        product.description = product_update.description
    if product_update.price is not None:
        product.price = product_update.price
    if product_update.stock is not None:
        product.stock = product_update.stock
    if product_update.currency is not None:
        # Check if the currency is supported
        list_of_supported_currencies = ["Us Dollar", "Franc CFA", "Euro", "Naira", "Rouble", "Yuan", "Yen", "Pound Sterling", "Rand", "Rupee", "Real", "Peso", "Dinar", "Dirham", "Krone", "Krona", "Forint", "Kuna", "Koruna", "Lira", "Leu", "Lek", "Lira", "Marka", "Pataca", "Peso", "Pula", "Rial", "Riyal", "Rufiyaa", "Rupiah", "Shekel", "Taka", "Tenge", "Tugrik", "Won", "Zloty", "Baht"]
        if product_update.currency not in list_of_supported_currencies:
            raise HTTPException(status_code=400, detail="The currency is not supported")
        product.currency = product_update.currency

    # Handle categories if provided
    if product_update.category_ids:
        # Get existing categories
        existing_categories = db.query(ProductCategory).filter(
            ProductCategory.product_id == product.id
        ).all()
        existing_category_ids = {pc.category_id for pc in existing_categories}

        # Add new categories
        for category_id in product_update.category_ids:
            if category_id not in existing_category_ids:
                category = db.query(Category).filter(Category.id == category_id).first()
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
    if product_update.images:
        # Get existing images count
        existing_images = db.query(ProductImage).filter(
            ProductImage.product_id == product.id
        ).all()
        
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
                s.minio_bucket, 
                f"products/{image.filename}"
            )
            new_image = ProductImage(
                product_id=product.id, 
                image_url=image_url
            )
            db.add(new_image)

    # Commit changes
    db.commit()
    db.refresh(product)

    # Get updated categories and images
    categories = []
    for pc in db.query(ProductCategory).filter(ProductCategory.product_id == product.id).all():
        category = db.query(Category).filter(Category.id == pc.category_id).first()
        if category:
            categories.append(Category(id=category.id, name=category.name))
    
    images = []
    for pi in db.query(ProductImage).filter(ProductImage.product_id == product.id).all():
        images.append(ProductImageSchema(id=pi.id, image_url=pi.image_url))

    return ProductResponse(
        id=product.id,
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock,
        categories=categories,
        images=images,
        currency=product.currency
    )



async def delete_product(db: Session, product_id: int, user_id: int):
    # check if the product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    # check if it is the seller who is deleting the product
    if product.seller_id != user_id:
        raise HTTPException(status_code=403, detail="You are not allowed to delete this product")
    # delete the product images
    for image in product.images:
        # get image unique name by removing the url
        image_unique_name = image.image_url.split("/")[-1]
        log.info(f"Deleting image {image_unique_name} from {s.minio_bucket}")
        await delete_file(s.minio_bucket, image_unique_name)
    # delete product categories
    db.query(ProductCategory).filter(ProductCategory.product_id == product.id).delete()
    db.commit()
    # delete the product
    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


# get a product with its discounts
async def get_product_with_discounts(db: Session, product_id: int):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # check if the product has an active discount
    current_time = get_utc_now()
    discount = db.query(Discount).filter(
        Discount.product_id == product.id,
        Discount.start_date <= current_time,
        Discount.end_date > current_time
    ).first()

    # Use the new helper method to create the response
    return ProductWithDiscount.from_orm_with_discount(product, discount)

