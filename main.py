from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, Cookie, HTTPException, Request, Depends, status, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
import re
import jwt
from data import *
from models import Feedback, Todo
from db.tools import SqliteTools

app = FastAPI(
    title="New app"
)

SECRET_KEY = "abc123xyz456"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
ALGORITHM = "HS256"


def create_jwt_token(payload: dict):
    payload.update({'exp': (datetime.now() +
                            timedelta(minutes=30)).timestamp()})
    return jwt.encode(payload=payload, key=SECRET_KEY, algorithm='HS256')


def get_user_from_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token has expired",
                            headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token",
                            headers={"WWW-Authenticate": "Bearer"})


def get_user(username: str):
    if username in USERS_DATA:
        return User(**USERS_DATA[username])
    return None


@app.post("/token")
async def login(user: Annotated[OAuth2PasswordRequestForm, Depends()]):
    cur_user = get_user(user.username)
    if cur_user is None or cur_user.password != user.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid user",
                            headers={"WWW-Authenticate": "Bearer"}
                            )
    return {"access_token": create_jwt_token({"sub": cur_user.username})}


@app.get("/create")
async def create(current_user: str = Depends(get_user_from_token)):
    user_data = get_user(current_user)
    if user_data.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Forbidden"
                            )
    return {"message": f"Successful create!"}


@app.get("/read")
async def read(current_user: str = Depends(get_user_from_token)):
    user_data = get_user(current_user)
    if user_data.role not in ("admin", "user", "guest"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Forbidden"
                            )
    return {"message": f"Successful read!"}


@app.get("/update")
async def update(current_user: str = Depends(get_user_from_token)):
    user_data = get_user(current_user)
    if user_data.role not in ("admin", "user"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Forbidden"
                            )
    return {"message": f"Successful update!"}


@app.get("/delete")
async def delete(current_user: str = Depends(get_user_from_token)):
    user_data = get_user(current_user)
    if user_data.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Forbidden"
                            )
    return {"message": f"Successful delete!"}


@app.get("/feedback")
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


@app.get("/todo/{todo_id}", response_model=Todo)
async def get_todo_list(todo_id: int):
    todo = SqliteTools.get_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Todo not found")
    return todo


@app.post("/todo")
async def create_todo_list(todo_data: Todo):
    todo = SqliteTools.add_todo(todo_data.title, todo_data.description)
    return todo


@app.put("/todo/{todo_id}")
async def update_todo_list(todo_id: int, todo_data: Todo):
    todo = SqliteTools.update_todo_by_id(todo_id, todo_data.title, todo_data.description, todo_data.completed)
    return todo


@app.delete("/todo/{todo_id}")
async def delete_todo_list(todo_id: int):
    deleted = SqliteTools.delete_todo_by_id(todo_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Todo not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    SqliteTools.check_exists_db()
    uvicorn.run(
        app="main:app", host="127.0.0.1", port=8000, workers=3, reload=True
    )