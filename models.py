from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from datetime import datetime
import os
from extensions import db

db = SQLAlchemy() 

# Creating models
# Products model
class Product(db.Model):
    __tablename__='products'
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String,nullable=False)
    buying_price=db.Column(db.Float,nullable=False)
    selling_price=db.Column(db.Float,nullable=False)

    sales=db.relationship('Sale',backref='product')

# Sales model
class Sale(db.Model):
    __tablename__='sales'
    id=db.Column(db.Integer,primary_key=True)
    pid=db.Column(db.Integer,db.ForeignKey('products.id'),nullable=False)
    quantity=db.Column(db.Integer,nullable=False)
    created_at=db.Column(db.DateTime,nullable=False)

# User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)

# Payment model
class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, nullable=False)
    mrid = db.Column(db.String(100), nullable=False)
    crid = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=True)
    trans_code = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



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
