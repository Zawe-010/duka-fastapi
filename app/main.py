from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from datetime import datetime
import json

from app.models import Product, Sale, User, Payment, session
from app.auth.auth_service import get_current_user
from app.auth.auth_routes import router as auth_router
from app.mpesa import send_stk_push  

from pydantic import BaseModel

app = FastAPI()
db = session()

# --- CORS ---
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://172.26.80.1:3001",
    "https://my-duka.co.ke",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include auth routes ---
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
    product_name: str
    product_sp: float
    amount: float

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

# --- MPesa Request Body Model ---
class STKPushRequest(BaseModel):
    amount: float
    phone_number: str
    sale_id: int

# --- Routes ---
@app.get("/")
def home():
    return {"Duka FastAPI": "1.0"}

# --- Products ---
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

@app.put("/products/{product_id}", response_model=ProductDataResponse)
def update_product(
    product_id: int,
    prod: ProductData,
    current_user: User = Depends(get_current_user)
):
    db_prod = db.query(Product).filter(Product.id == product_id).first()

    if not db_prod:
        raise HTTPException(status_code=404, detail="Product not found")

    db_prod.name = prod.name
    db_prod.buying_price = prod.buying_price
    db_prod.selling_price = prod.selling_price

    db.commit()
    db.refresh(db_prod)

    return db_prod

# --- Sales ---
@app.get("/sales", response_model=List[SaleDataResponse])
def get_sales(current_user: User = Depends(get_current_user)):
    sales = db.query(Sale).all()
    response = []

    for sale in sales:
        product = db.query(Product).filter(Product.id == sale.pid).first()
        if not product:
            continue
        response.append(SaleDataResponse(
            id=sale.id,
            pid=sale.pid,
            quantity=sale.quantity,
            created_at=sale.created_at,
            product_name=product.name,
            product_sp=product.selling_price,
            amount=sale.quantity * product.selling_price
        ))
    return response

@app.post("/sales", response_model=SaleDataResponse)
def add_sale(sale: SaleData, current_user: User = Depends(get_current_user)):
    try:
        db_sale = Sale(pid=sale.pid, quantity=sale.quantity, created_at=sale.created_at)
        db.add(db_sale)
        db.commit()
        db.refresh(db_sale)

        product = db.query(Product).filter(Product.id == db_sale.pid).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return SaleDataResponse(
            id=db_sale.id,
            pid=db_sale.pid,
            quantity=db_sale.quantity,
            created_at=db_sale.created_at,
            product_name=product.name,
            product_sp=product.selling_price,
            amount=db_sale.quantity * product.selling_price
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# --- Dashboard ---
@app.get("/dashboard")
def dashboard(current_user: User = Depends(get_current_user)):
    # Profit per product
    profit_product = db.execute(text("""
        SELECT p.name, 
               SUM((p.selling_price - p.buying_price) * s.quantity) AS profit
        FROM sales s
        JOIN products p ON s.pid = p.id
        GROUP BY p.id
    """)).fetchall()

    # Sales per day
    sales_day = db.execute(text("""
        SELECT DATE(s.created_at) AS date,
               SUM(p.selling_price * s.quantity) AS sales
        FROM sales s
        JOIN products p ON s.pid = p.id
        GROUP BY date
        ORDER BY date
    """)).fetchall()

    def generate_colors(n):
        return [f"hsl({int(360*i/n)}, 70%, 50%)" for i in range(n)]

    products_name = [row[0] for row in profit_product]
    products_sales = [float(row[1]) for row in profit_product]
    products_colour = generate_colors(len(profit_product))

    dates = [row[0].strftime("%Y-%m-%d") for row in sales_day]
    sales = [float(row[1]) for row in sales_day]

    data = {
        "profit_per_product": {
            "products_name": products_name,
            "products_sales": products_sales,
            "products_colour": products_colour
        },
        "sales_per_day": {
            "dates": dates,
            "sales": sales
        }
    }
    return JSONResponse(content=data)

# --- Users ---
@app.get("/users", response_model=List[UserDataResponse])
def get_users(current_user: User = Depends(get_current_user)):
    return db.query(User).all()

# --- Payments ---
@app.get("/payments", response_model=List[PaymentDataResponse])
def get_payments(current_user: User = Depends(get_current_user)):
    payments = db.query(Payment).all()
    response = []

    for p in payments:
        sale = db.query(Sale).filter(Sale.id == p.sale_id).first()
        product = db.query(Product).filter(Product.id == sale.pid).first() if sale else None
        response.append(PaymentDataResponse(
            id=p.id,
            sale_id=p.sale_id,
            mrid=p.mrid,
            crid=p.crid,
            amount=p.amount,
            trans_code=p.trans_code,
            created_at=p.created_at
        ))
    return response

# --- MPesa STK Push ---
@app.post("/mpesa/stkpush")
def mpesa_stk_push(data: STKPushRequest, current_user: User = Depends(get_current_user)):
    res = send_stk_push(data.amount, data.phone_number, data.sale_id)
    mrid = res.get("MerchantRequestID")
    crid = res.get("CheckoutRequestID")

    if not mrid or not crid:
        raise HTTPException(status_code=400, detail="Failed to initiate M-Pesa STK Push")

    payment = Payment(
        sale_id=data.sale_id,
        mrid=mrid,
        crid=crid,
        amount=0,        # will be updated later in callback
        trans_code="PENDING",
        created_at=datetime.utcnow()
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {"mpesa_response": res, "payment_record_id": payment.id}

# --- MPesa Callback ---
@app.post("/mpesa/callback")
def mpesa_callback(data: dict):
    try:
        stk_callback = data.get("Body", {}).get("stkCallback")
        if not stk_callback:
            return {"error": "Invalid callback format"}

        mrid = stk_callback.get("MerchantRequestID")
        crid = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")

        payment = db.query(Payment).filter_by(mrid=mrid, crid=crid).first()
        if not payment:
            return {"error": "Payment record not found"}

        if result_code == 0:
            # Payment successful
            items = stk_callback.get("CallbackMetadata", {}).get("Item", [])
            amount = next((i.get("Value") for i in items if i.get("Name") == "Amount"), None)
            trans_code = next((i.get("Value") for i in items if i.get("Name") in ["MpesaReceiptNumber", "ReceiptNumber"]), None)
            payment.amount = float(amount) if amount else 0
            payment.trans_code = trans_code or "N/A"
        else:
            payment.amount = 0
            payment.trans_code = "FAILED"

        db.commit()
        return {"success": True}

    except Exception as e:
        return {"error": str(e)}

# --- MPesa Checker ---
@app.get("/mpesa/checker/{sale_id}")
def mpesa_checker(sale_id: int):
    payment = db.query(Payment).filter_by(sale_id=sale_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {
        "trans_code": payment.trans_code,
        "amount": payment.amount
    }

# Why use fastapi?
# 1. Type hints - We can validate the data type expected by a route.
# 2. Pydantic model - Classes/Objects which convert JSON to an object and Pydantic to validate.
# 3. Async/Await - Performs a heavy task like upload a file asynchronously.
# 4. Swagger library - To document and test your API routes.