from pydantic import BaseModel
from typing import List, Optional

# Modèle pour les catégories
class Category(BaseModel):
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True