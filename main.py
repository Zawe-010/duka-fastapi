from typing import List
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime
from models import Product, Sale, User, Payment, session
from auth.auth_routes import router as auth_router
from auth.auth_service import get_current_user

app = FastAPI()
db = session()

# Include auth routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# --- Pydantic Models ---
class ProductData(BaseModel):
    name: str
    buying_price: float
    selling_price: float

class ProductDataResponse(ProductData):
    id: int

class SaleData(BaseModel):
    pid: int
    quantity: int
    created_at: datetime = datetime.utcnow()

class SaleDataResponse(SaleData):
    id: int

class UserData(BaseModel):
    full_name: str
    email: str
    password: str

class UserDataResponse(UserData):
    id: int

class PaymentData(BaseModel):
    sale_id: int
    mrid: str
    crid: str
    amount: float | None = None
    trans_code: str | None = None
    created_at: datetime = datetime.utcnow()

class PaymentDataResponse(PaymentData):
    id: int

# --- Routes ---
@app.get("/")
def home():
    return {"Duka FastAPI": "1.0"}

# Products
@app.get("/products", response_model=List[ProductDataResponse])
def get_products(current_user: User = Depends(get_current_user)):
    return db.query(Product).all()

@app.post("/products", response_model=ProductDataResponse)
def add_product(prod: ProductData, current_user: User = Depends(get_current_user)):
    db_prod = Product(**prod.dict())
    db.add(db_prod)
    db.commit()
    db.refresh(db_prod)
    return db_prod

# Sales
@app.get("/sales", response_model=List[SaleDataResponse])
def get_sales(current_user: User = Depends(get_current_user)):
    return db.query(Sale).all()

@app.post("/sales", response_model=SaleDataResponse)
def add_sale(sale: SaleData, current_user: User = Depends(get_current_user)):
    db_sale = Sale(**sale.dict())
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale

# Users 
@app.get("/users", response_model=List[UserDataResponse])
def get_users(current_user: User = Depends(get_current_user)):
    return db.query(User).all()

# Payments
@app.get("/payments", response_model=List[PaymentDataResponse])
def get_payments(current_user: User = Depends(get_current_user)):
    return db.query(Payment).all()

@app.post("/payments", response_model=PaymentDataResponse)
def add_payment(payment: PaymentData, current_user: User = Depends(get_current_user)):
    db_payment = Payment(**payment.dict())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return db_payment

# Why use fastapi?
# 1. Type hints - We can validate the data type expected by a route.
# 2. Pydantic model - Classes/Objects which convert JSON to an object and Pydantic to validate.
# 3. Async/Await - Performs a heavy task like upload a file asynchronously.
# 4. Swagger library - To document and test your API routes.