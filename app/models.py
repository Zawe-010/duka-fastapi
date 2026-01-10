from sqlalchemy import create_engine, Integer, String, Float, Column, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from datetime import datetime

engine = create_engine('postgresql://flask_api_user:Zawadi06zara@172.17.0.1:5432/flask_api')
# engine = create_engine('postgresql://postgres:Zawadi%402006#@localhost:5432/flask_api')
session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Creating models
# Product model
class Product(Base):
    __tablename__='products'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    buying_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)

# Sale model
class Sale(Base):
    __tablename__='sales'
    id = Column(Integer, primary_key=True)
    pid = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship for multiple products per sale
    details = relationship("SalesDetails", back_populates="sale")
    payments = relationship("Payment", back_populates="sale")

# SalesDetails model
class SalesDetails(Base):
    __tablename__='sales_details'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sale = relationship("Sale", back_populates="details")

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)  # Optional SMS OTP
    password = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
        
    otps = relationship("OTP", backref="user", cascade="all, delete-orphan")


# OTP model
class OTP(Base):
    __tablename__='otps'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    otp = Column(String(4), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Payment model
class Payment(Base):
    __tablename__='payments'
    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey('sales.id'), nullable=False)
    mrid = Column(String(100), nullable=False)
    crid = Column(String(100), nullable=False)
    amount = Column(Float, nullable=True)
    trans_code = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    sale = relationship("Sale", back_populates="payments")

# This is the correct way to create tables
Base.metadata.create_all(bind=engine)


# from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
# from sqlalchemy.orm import relationship, declarative_base
# from datetime import datetime

# Base = declarative_base()

# class Product(Base):
#     __tablename__ = 'products'
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, nullable=False)
#     buying_price = Column(Float, nullable=False)
#     selling_price = Column(Float, nullable=False)
    
#     sales = relationship("Sale", back_populates="product")

# class Sale(Base):
#     __tablename__ = 'sales'
#     id = Column(Integer, primary_key=True, index=True)
#     pid = Column(Integer, ForeignKey('products.id'), nullable=False)
#     quantity = Column(Integer, nullable=False)
#     created_at = Column(DateTime, default=datetime.utcnow)
    
#     product = relationship("Product", back_populates="sales")

# class User(Base):
#     __tablename__ = 'users'
#     id = Column(Integer, primary_key=True, index=True)
#     full_name = Column(String, nullable=False)
#     email = Column(String, unique=True, nullable=False)
#     password = Column(String, nullable=False)

# class Payment(Base):
#     __tablename__ = 'payments'
#     id = Column(Integer, primary_key=True, index=True)
#     sale_id = Column(Integer, nullable=False)
#     mrid = Column(String(100), nullable=False)
#     crid = Column(String(100), nullable=False)
#     amount = Column(Float, nullable=True)
#     trans_code = Column(String(100), nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)
