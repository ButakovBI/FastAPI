from fastapi import FastAPI, Cookie, Response, HTTPException
from models import *

app = FastAPI()

sample_user: dict = {"name": "user123", "password": "password123"}
users: list[User] = [User(**sample_user)]
sessions = {}

sample_product_1 = {
    "product_id": 123,
    "name": "Smartphone",
    "category": "Electronics",
    "price": 599.99
}

sample_product_2 = {
    "product_id": 456,
    "name": "Phone Case",
    "category": "Accessories",
    "price": 19.99
}

sample_product_3 = {
    "product_id": 789,
    "name": "Iphone",
    "category": "Electronics",
    "price": 1299.99
}

sample_product_4 = {
    "product_id": 101,
    "name": "Headphones",
    "category": "Accessories",
    "price": 99.99
}

sample_product_5 = {
    "product_id": 202,
    "name": "Smartwatch",
    "category": "Electronics",
    "price": 299.99
}

sample_products = [sample_product_1, sample_product_2, sample_product_3, sample_product_4, sample_product_5]

feedbacks = [
    {
        "name": "Bogdan",
        "message": "OK"
    }
]


# @app.post("/create_user")
# async def create_user(user: UserCreate):
#     users.append(user)
#     return user


@app.post("/feedback")
async def add_feedback(feedback: Feedback):
    feedbacks.append({"name": feedback.name, "message": feedback.message})
    return f"Feedback received. Thank you, {feedback.name}!"


@app.get("/comments")
async def get_all_feedbacks():
    return feedbacks


@app.get("/product/{product_id}")
async def get_product(product_id: int):
    for product in sample_products:
        if product["product_id"] == product_id:
            return product
    return {"message": "Product not found"}


@app.get("/products/search")
async def search_product(keyword: str, category: str = None, limit: int = 10):
    ans = [product for product in sample_products if (keyword.lower() in product["name"].lower() and
                                                      category.lower() == product["category"].lower())]
    return ans[:limit]


@app.post('/login')
async def login(user: User, response: Response):
    for person in users:
        if person.name == user.name and person.password == user.password:
            session_token = "abc123xyz456"
            sessions[session_token] = user
            response.set_cookie(key="session_token", value=session_token, httponly=True)
            return {"message": "куки установлены"}
    return {"message": "Invalid username or password"}


@app.get("/user")
async def user_info(session_token=Cookie()):
    user = sessions.get(session_token)
    if user:
        return user.dict()
    raise HTTPException(status_code=401, detail="not found")
