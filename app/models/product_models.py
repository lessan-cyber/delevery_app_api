from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Table,
    ForeignKey,
    Text,
    TIMESTAMP,
    DECIMAL,
    Float,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    products = relationship(
        "Product",
        secondary="product_categories",
        back_populates="categories",
        overlaps="product_categories,product",
    )

    def __repr__(self):
        return f"<Category(name={self.name}, description={self.description})>"


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    image_url = Column(String(255), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    product = relationship("Product", back_populates="images")

    def __repr__(self):
        return f"<ProductImage(image_url={self.image_url})>"


class Discount(Base):
    __tablename__ = "discounts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    discount_percentage = Column(DECIMAL(5, 2), nullable=False)
    start_date = Column(TIMESTAMP(timezone=True), nullable=False)
    end_date = Column(TIMESTAMP(timezone=True), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    product = relationship("Product", back_populates="discounts")

    def __repr__(self):
        return f"<Discount(percentage={self.discount_percentage})>"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    image_url = Column(String(255), nullable=True)
    stock = Column(Integer, nullable=False, default=0)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    currency = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(
        TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    categories = relationship(
        "Category",
        secondary="product_categories",
        back_populates="products",
        overlaps="product_categories,product",
    )
    images = relationship(
        "ProductImage", back_populates="product", cascade="all, delete"
    )

    product_categories = relationship(
        "ProductCategory", back_populates="product", overlaps="categories,products"
    )
    discounts = relationship(
        "Discount", back_populates="product", cascade="all, delete"
    )

    def __repr__(self):
        return f"<Product(name={self.name}, price={self.price})>"


class ProductCategory(Base):
    __tablename__ = "product_categories"

    product_id = Column(Integer, ForeignKey("products.id"), primary_key=True)
    category_id = Column(Integer, ForeignKey("categories.id"), primary_key=True)

    product = relationship(
        "Product", back_populates="product_categories", overlaps="categories,products"
    )
    category = relationship("Category", overlaps="products,categories")
