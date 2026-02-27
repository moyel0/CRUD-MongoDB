from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List
app = FastAPI()
client = MongoClient("mongodb://localhost:27017")
db = client["users_db"]
users_collection = db["users"]

class User(BaseModel):
    first_name: str = Field(..., alias="Имя")           # [cite: 3]
    last_name: str = Field(..., alias="Фамилия")        # [cite: 4]
    email: EmailStr = Field(..., alias="Электронная почта") # [cite: 5]
    registration_date: datetime = Field(default_factory=datetime.now, alias="Дата регистрации") # [cite: 6]

    class Config:
        populate_by_name = True

def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "first_name": user.get("first_name") or user.get("Имя"),
        "last_name": user.get("last_name") or user.get("Фамилия"),
        "email": user.get("email") or user.get("Электронная почта"),
        "registration_date": user.get("registration_date") or user.get("Дата регистрации")
    }
@app.post("/users/", status_code=201)
async def create_user(user: User):
    user_dict = user.dict(by_alias=True)
    result = users_collection.insert_one(user_dict)
    return {"id": str(result.inserted_id), "message": "Пользователь успешно создан"}
@app.get("/users/", response_model=List[dict])
async def get_all_users():
    users = []
    for user in users_collection.find():
        users.append(user_helper(user))
    return users

@app.get("/users/{user_id}")
async def get_user_by_id(user_id: str):
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        return user_helper(user)
    raise HTTPException(status_code=404, detail="Пользователь не найден")
@app.put("/users/{user_id}")
async def update_user(user_id: str, update_data: dict):
    # Обновляем только те поля, которые прислал пользователь
    result = users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    if result.modified_count == 1:
        return {"message": "Данные обновлены"}
    raise HTTPException(status_code=404, detail="Пользователь не найден или данные идентичны")
@app.delete("/users/{user_id}")
async def delete_user(user_id: str):
    result = users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 1:
        return {"message": "Пользователь удален"}
    raise HTTPException(status_code=404, detail="Пользователь не найден")