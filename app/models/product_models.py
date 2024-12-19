from sqlalchemy import Column, Integer, String, Boolean, DateTime, Table, ForeignKey, Text, TIMESTAMP, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)

    # Relation avec les produits via la table de liaison
    products = relationship('Product', secondary='product_categories', back_populates='categories')

    def __repr__(self):
        return f"<Category(name={self.name}, description={self.description})>"
    


class ProductImage(Base):
    __tablename__ = 'product_images'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    image_url = Column(String(255), nullable=False)  # URL ou chemin de l'image
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)  # Référence au produit
    
    # Relation avec le produit
    product = relationship('Product', back_populates='images')

    def __repr__(self):
        return f"<ProductImage(image_url={self.image_url})>"


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(DECIMAL(10, 2), nullable=False)
    image_url = Column(String(255), nullable=True)  # Optionnel, si tu veux une image principale
    stock = Column(Integer, nullable=False, default=0)
    discount = Column(DECIMAL(3, 2), nullable=True)
    seller_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    currency = Column(String(50), nullable = False )
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relation many-to-many avec les catégories
    categories = relationship('Category', secondary='product_categories', back_populates='products')

    # Relation one-to-many avec les images du produit
    images = relationship('ProductImage', back_populates='product', cascade='all, delete')

    def __repr__(self):
        return f"<Product(name={self.name}, price={self.price})>"
    
class ProductCategory(Base):
    __tablename__ = 'product_categories'

    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'), primary_key=True)