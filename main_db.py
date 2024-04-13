import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from databases import Database
from models import UserCreate, UserReturn, ErrorResponse


app = FastAPI()

DATABASE_URL = "postgresql://postgres:test@localhost/postgres"

database = Database(DATABASE_URL)


async def create_table():
    sql_query = ("CREATE TABLE product (id SERIAL PRIMARY KEY,"
                 "title VARCHAR(255) NOT NULL,"
                 "price INTEGER NOT NULL,"
                 "count INTEGER NOT NULL);")
    await database.execute(sql_query)


@app.on_event("startup")
async def startup_database():
    await database.connect()


@app.on_event("shutdown")
async def shutdown_database():
    await database.disconnect()


@app.post("/users/", response_model=UserReturn)
async def create_user(user: UserCreate):
    query = "INSERT INTO users (username, email) VALUES (:username, :email) RETURNING id"
    values = {"username": user.username, "email": user.email}
    try:
        user_id = await database.execute(query=query, values=values)
        return {**user.model_dump(), "id": user_id}
    except Exception:
        raise HTTPException(status_code=500, detail=f"Failed to create user")


@app.get("/user/{user_id}", response_model=UserReturn)
async def get_user(user_id: int):
    query = "SELECT * FROM users WHERE id = :user_id"
    values = {"user_id": user_id}
    try:
        result = await database.fetch_one(query=query, values=values)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch user from database")
    if result:
        return UserReturn(username=result["username"], email=result["email"], id=result["id"])
    else:
        raise HTTPException(status_code=404, detail="User not found")


@app.put("/user/{user_id}", response_model=UserReturn)
async def update_user(user_id: int, user: UserCreate):
    query = "UPDATE users SET username = :username, email = :email WHERE id = :user_id"
    values = {"user_id": user_id, "username": user.username, "email": user.email}
    try:
        await database.execute(query=query, values=values)
        return {**user.model_dump(), "id": user_id}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update user in database")


@app.delete("/user/{user_id}", response_model=dict)
async def delete_user(user_id: int):
    query = "DELETE FROM users WHERE id = :user_id RETURNING id"
    values = {"user_id": user_id}
    try:
        deleted_rows = await database.execute(query=query, values=values)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to delete user from database")
    if deleted_rows:
        return {"message": "User deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="User not found")


class CustomException1(HTTPException):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(detail=detail, status_code=status_code)


class CustomException2(HTTPException):
    def __init__(self):
        super().__init__(detail="Internal server errorrrrrrr", status_code=500)


@app.exception_handler(CustomException1)
async def custom_exception_1(request: Request, exc: ErrorResponse):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(CustomException2)
async def custom_exception_2(request: Request, exc: ErrorResponse):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500,
                        content="Internal server error")


@app.get("/raise")
async def get_exception(number: int):
    if number == 794:
        raise CustomException1(detail="WOW", status_code=403)
    if number == 793:
        raise CustomException2
    raise Exception


if __name__ == "__main__":
    uvicorn.run(
        app="main_db:app", host="127.0.0.1", port=8000, workers=3, reload=True
    )
