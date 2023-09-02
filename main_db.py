import uvicorn
from fastapi import FastAPI, HTTPException
from databases import Database
from models import UserCreate, UserReturn

app = FastAPI()

# URL для PostgreSQL (измените его под свою БД)
DATABASE_URL = "postgresql://postgres:794794@localhost/postgres"

database = Database(DATABASE_URL)


async def create_table():
    sql_query = ("CREATE TABLE users (id SERIAL PRIMARY KEY,"
                 "username VARCHAR(255) NOT NULL,"
                 "email VARCHAR(255) NOT NULL);")
    await database.execute(sql_query)


# тут устанавливаем условия подключения к базе данных и отключения - можно использовать в роутах
# контекстный менеджер async with Database(...) as db: etc
@app.on_event("startup")
async def startup_database():
    await database.connect()


@app.on_event("shutdown")
async def shutdown_database():
    await database.disconnect()


# создание роута для создания юзеров
@app.post("/users/", response_model=UserReturn)
async def create_user(user: UserCreate):
    query = "INSERT INTO users (username, email) VALUES (:username, :email) RETURNING id"
    values = {"username": user.username, "email": user.email}
    try:
        user_id = await database.execute(query=query, values=values)
        return {**user.model_dump(), "id": user_id}
    except Exception:
        raise HTTPException(status_code=500, detail=f"Failed to create user")


# маршрут для получения информации о юзере по ID
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


# роут для обновления информации о юзере по ID
@app.put("/user/{user_id}", response_model=UserReturn)
async def update_user(user_id: int, user: UserCreate):
    query = "UPDATE users SET username = :username, email = :email WHERE id = :user_id"
    values = {"user_id": user_id, "username": user.username, "email": user.email}
    try:
        await database.execute(query=query, values=values)
        return {**user.model_dump(), "id": user_id}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update user in database")


# роут для удаления информации о юзере по ID
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


if __name__ == "__main__":
    uvicorn.run(
        app="main_db:app", host="127.0.0.1", port=8000, workers=3, reload=True
    )
