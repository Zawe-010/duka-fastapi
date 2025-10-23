from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from models import  Product, session, Sale, User, Payment
from datetime import datetime



# Sentry / Slack / SQLAlchemy / Unit Test / Gitflow workflow / Jira / CICD /Docker

app = FastAPI()
db = session()


class ProductData(BaseModel):
    name : str
    buying_price : float
    selling_price : float

class ProductDataResponse(ProductData):
    id : int

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

class UserLogin(BaseModel):
    email: str
    password: str

class UserLoginResponse(UserLogin):
    full_name: str

class PaymentData(BaseModel):
    sale_id: int
    mrid: str
    crid: str
    amount: float | None = None
    trans_code: str | None = None
    created_at: datetime = datetime.utcnow()

class PaymentDataResponse(PaymentData):
    id: int

@app.get("/")
def home():
    return {"Duka FastAPI": "1.0"}

@app.get("/products", response_model=list[ProductDataResponse])
def get_products():
    return db.query(Product).all()

@app.post("/products", response_model=ProductDataResponse)
def add_product(prod : ProductData):
    db_prod = Product(**prod.dict())
    db.add(db_prod)
    db.commit()
    return db_prod

@app.get("/sales", response_model=list[SaleDataResponse])
def get_sales():
    return db.query(Sale).all()


@app.post("/sales", response_model=SaleDataResponse)
def add_sale(sale: SaleData):
    db_sale = Sale(**sale.dict())
    db.add(db_sale)
    db.commit()
    return db_sale

@app.get("/users", response_model=list[UserDataResponse])
def get_users():
    return db.query(User).all()

@app.post("/users", response_model=UserDataResponse)
def add_user(user: UserData):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    return db_user

@app.post("/login", response_model=UserLoginResponse)
def user_login(userLogin: UserLogin):
    db_login = db.query(User).filter(User.email == userLogin.email, User.password == userLogin.password).first()
    if not db_login:
        return "Invalid credentials"
    return db_login

@app.get("/payments", response_model=list[PaymentDataResponse])
def get_payments():
    return db.query(Payment).all()

@app.post("/payments", response_model=PaymentDataResponse)
def add_payment(payment: PaymentData):
    db_payment = Payment(**payment.dict())
    db.add(db_payment)
    db.commit()
    return db_payment


# Why use fastapi?
# 1. Type hints - We can validate the data type expected by a route.
# 2. Pydantic model - Classes/Objects which convert JSON to an object and Pydantic to validate.
# 3. Async/Await - Performs a heavy task like upload a file asynchronously.
# 4. Swagger library - To document and test your API routes.