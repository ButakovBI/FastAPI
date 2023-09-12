from datetime import datetime, timedelta

from fastapi import FastAPI, Cookie, HTTPException, Request, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from databases import Database
import re
import jwt
from data import *
from models import *


app = FastAPI(
    title="New app"
)

DATABASE_URL = "postgresql://postgres:794794@localhost/postgres"
database = Database(DATABASE_URL)

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


@app.get("/files/{file_path:path}")
async def read_file(file_path: str):
    return {"file_path": file_path}


async def create_table():
    query = ("CREATE TABLE todos (id SERIAL PRIMARY KEY,"
             "title VARCHAR NOT NULL,"
             "description VARCHAR,"
             "completed BOOLEAN);")
    await database.execute(query)


@app.on_event("startup")
async def startup_database():
    await database.connect()


@app.on_event("shutdown")
async def shutdown_database():
    await database.disconnect()


@app.post("/create_todo")
async def create_todo(todo: TodoCreate):
    query = ("INSERT INTO todos(title, description, completed)"
             "VALUES (:title, :description, :completed)"
             "RETURNING id")
    values = {"title": todo.title, "description": todo.description, "completed": todo.completed}
    try:
        todo_id = await database.execute(query=query, values=values)
        return {**todo.model_dump(), "id": todo_id}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to create todo")


@app.get("/todo/{todo_id}", response_model=TodoReturn)
async def read_todo(todo_id: int):
    query = "SELECT * FROM todos WHERE id = :todo_id"
    values = {"todo_id": todo_id}
    try:
        result = await database.fetch_one(query=query, values=values)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to fetch todo from database")
    if result:
        return TodoReturn(id=result["id"], title=result["title"],
                          description=result["description"], completed=result["completed"])
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Todo not found")


@app.put("/todo/{todo_id}", response_model=TodoReturn)
async def update_todo(todo_id: int, todo: TodoCreate):
    query = "UPDATE todos SET title = :title, description = :description, completed = :completed WHERE id = :id"
    values = {"id": todo_id, "title": todo.title, "description": todo.description, "completed": todo.completed}
    try:
        await database.execute(query=query, values=values)
        return {**todo.model_dump(), "id": todo_id}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update todo in database")


@app.delete("/todo/{todo_id}")
async def delete_todo(todo_id: int):
    query = "DELETE FROM todos WHERE id = :id RETURNING id"
    values = {"id": todo_id}
    try:
        deleted_rows = await database.execute(query=query, values=values)
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to delete todo from database")
    if deleted_rows:
        return {"message": "Todo deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Todo not found")


# if __name__ == "__main__":
#     SqliteTools.check_exists_db()
#     uvicorn.run(
#         app="main:app", host="127.0.0.1", port=8000, workers=3, reload=True
#     