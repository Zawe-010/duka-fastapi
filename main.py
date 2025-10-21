from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from models import  Product, session


# Sentry / Slack / SQLAlchemy / Unit Test / Gitflow workflow / Jira / CICD /Docker

app = FastAPI()
db = session()


class ProductData(BaseModel):
    name : str
    buying_price : float
    selling_price : float


class ProductDataResponse(ProductData):
    id : int


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


# Why use fastapi?
# 1. Type hints - We can validate the data type expected by a route.
# 2. Pydantic model - Classes/Objects which convert JSON to an object and Pydantic to validate.
# 3. Async/Await - Performs a heavy task like upload a file asynchronously.
# 4. Swagger library - To document and test your API routes.