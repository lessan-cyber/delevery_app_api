from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Table,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


"""role_permissions = Table(
    "role_permission", Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id"), primary_key=True)
)"""


class User(Base):
    """
    User model for authentication and profile linkage.

    Use with AsyncSession and async SQLAlchemy operations.

    Attributes:
        id (int): Primary key.
        username (str): Unique username.
        email (str): Unique email address.
        phone_number (str): Unique phone number.
        hashed_password (str): Hashed user password.
        full_name (str): Full name of the user.
        is_active (bool): Whether the user is active.
        is_superuser (bool): Whether the user is a superuser.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
        role (str): User role (customer, driver, company, admin, etc.).
        preferred_currency (str): User's preferred currency (default: USD).
        customer_profile (CustomerProfile): One-to-one relationship.
        driver_profile (DriverProfile): One-to-one relationship.
        company_profile (CompanyProfile): One-to-one relationship.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    # role_id = Column(Integer, ForeignKey("roles.id"))
    # role = relationship("Role", back_populates="users")
    role = Column(String(50), nullable=False)
    customer_profile = relationship(
        "CustomerProfile", uselist=False, back_populates="user"
    )
    driver_profile = relationship("DriverProfile", uselist=False, back_populates="user")
    company_profile = relationship(
        "CompanyProfile", uselist=False, back_populates="user"
    )
    preferred_currency = Column(String(10), nullable=False, default="USD")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class CustomerProfile(Base):
    """
    Customer profile model.

    Use with AsyncSession and async SQLAlchemy operations.

    Attributes:
        user_id (int): Foreign key to User.
        default_address (str): Default address for deliveries.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
        user (User): Relationship to User.
    """
    __tablename__ = "customer_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    default_address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="customer_profile")


class DriverProfile(Base):
    """
    Driver profile model.

    Use with AsyncSession and async SQLAlchemy operations.

    Attributes:
        user_id (int): Foreign key to User.
        license_number (str): Driver's license number.
        vehicle_type (str): Type of vehicle.
        is_verified (bool): Whether the driver is verified.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
        user (User): Relationship to User.
    """
    __tablename__ = "driver_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    license_number = Column(String(50), nullable=False, unique=True, index=True)
    vehicle_type = Column(String(50), nullable=False, index=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User", back_populates="driver_profile")


class CompanyProfile(Base):
    """
    Company profile model.

    Use with AsyncSession and async SQLAlchemy operations.

    Attributes:
        user_id (int): Foreign key to User.
        company_name (str): Name of the company.
        business_type (str): Type of business.
        company_id (str): Unique company identifier.
        address (str): Company address.
        created_at (datetime): Creation timestamp.
        updated_at (datetime): Last update timestamp.
        user (User): Relationship to User.
    """
    __tablename__ = "company_profiles"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    company_name = Column(String(100), nullable=False, unique=True)
    business_type = Column(String(50))
    company_id = Column(String(50), unique=True, index=True)
    address = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    user = relationship("User", back_populates="company_profile")
