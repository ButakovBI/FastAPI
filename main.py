from datetime import datetime, timedelta
from fastapi import FastAPI, Cookie, Response, HTTPException, Request, Depends, status
from fastapi.security import HTTPBasic, OAuth2PasswordBearer
import re
import jwt
from data import *
from models import Feedback

app = FastAPI(
    title="New app"
)

security = HTTPBasic()
ACCESS_TOKEN_EXPIRE_MINUTES = 1
SECRET_KEY = "abc123xyz456"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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


# @app.post('/login')
# async def login(user: User, response: Response):
#     for person in users:
#         if person.name == user.username and person.password == user.password:
#             session_token = "abc123xyz456"
#             sessions[session_token] = user
#             response.set_cookie(key="session_token", value=session_token, httponly=True)
#             return {"message": "Set cookie"}
#     return {"message": "Invalid username or password"}


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


def authenticate_user(username, password):
    user = get_user_from_db(username)
    if user is None or user.password != password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials",
                            headers={"WWW-Authenticate": "Bearer"})
    return user


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encoded_jwt


@app.post("/login")
async def login(user: User):
    authenticate_user(user.username, user.password)
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/protected_resource")
async def protected_resource(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithm="HS256")
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"})
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Invalid token", headers={"WWW-Authenticate": "Bearer"})

    return {"message": "Access granted to protected resource"}
