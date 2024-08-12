
from pydantic import BaseModel
from typing import List
from .base import TimestampModel
from .users_schemas import User


class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleUpdate(RoleBase):
    pass

class RoleInDBBase(RoleBase, TimestampModel):
    id: int

class Role(RoleInDBBase):
    users: List['User'] = []
    permissions: List['Permission'] = []

    class Config:
        orm_mode = True

class PermissionBase(BaseModel):
    name: str

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(PermissionBase):
    pass

class PermissionInDBBase(PermissionBase, TimestampModel):
    id: int

class Permission(PermissionInDBBase):
    roles: List['Role'] = []

    class Config:
        orm_mode = True