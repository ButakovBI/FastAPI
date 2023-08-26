from fastapi import FastAPI, Cookie, Response, HTTPException, Request, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import re
from data import *
from models import Feedback

app = FastAPI(
    title="New app"
)

security = HTTPBasic()

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
        if person.name == user.username and person.password == user.password:
            session_token = "abc123xyz456"
            sessions[session_token] = user
            response.set_cookie(key="session_token", value=session_token, httponly=True)
            return {"message": "Set cookie"}
    return {"message": "Invalid username or password"}


@app.get("/user")
async def user_info(session_token=Cookie()):
    user = sessions.get(session_token)
    if user:
        return user.dict()
    raise HTTPException(status_code=401, detail="not found")


@app.get("/headers")
async def get_headers(request: Request):
    user_agent = request.headers.get("User-Agent")
    accept_language = request.headers.get("Accept-Language")
    if not (user_agent and accept_language):
        raise HTTPException(status_code=400, detail="Missing required headers")

    pattern = r"(?i:(?:\*|[a-z\-]{2,5})(?:;q=\d\.\d)?,)+(?:\*|[a-z\-]{2,5})(?:;q=\d\.\d)?"
    if not re.fullmatch(pattern, accept_language):
        raise HTTPException(status_code=400, detail="Wrong format of the Accept-Language header")

    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }


def get_user_from_db(username: str):
    for user in USER_DATA:
        if user.username == username:
            return user
    return None


def authenticate_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = get_user_from_db(credentials.username)
    if user is None or user.username != credentials.username or user.password != credentials.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


@app.get("/login")
async def protected_login(user: User = Depends(authenticate_user)):
    return {"message": "You got my secret, welcome",
            "user_info": user}
