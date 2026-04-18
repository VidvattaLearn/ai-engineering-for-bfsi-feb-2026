from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn


app = FastAPI(
    title="FastAPI Demo",
    description="Simple demo API for GET and POST requests.",
    version="1.0.0",
)


bank_balance: Dict[str, int] = {
    "8": 10000,
    "9": 6500,
}


class AddRequest(BaseModel):
    a: int = Field(..., description="First number")
    b: int = Field(..., description="Second number")


class MessageRequest(BaseModel):
    name: str = Field(..., description="Name of the caller")
    message: str = Field(..., description="Any message you want to send")


class WithdrawRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Amount to withdraw")


@app.get("/")
def read_root() -> dict:
    return {
        "message": "FastAPI demo is running",
        "docs": "/docs",
        "available_endpoints": [
            "GET /",
            "GET /health",
            "GET /users/{user_id}/balance",
            "POST /add",
            "POST /echo",
            "POST /users/{user_id}/withdraw",
        ],
    }


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/users/{user_id}/balance")
def get_bank_balance(user_id: str) -> dict:
    balance = bank_balance.get(user_id)
    if balance is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "balance": balance}


@app.post("/add")
def add_numbers(payload: AddRequest) -> dict:
    return {
        "a": payload.a,
        "b": payload.b,
        "result": payload.a + payload.b,
    }


@app.post("/echo")
def echo_message(payload: MessageRequest) -> dict:
    return {
        "reply": f"Hello {payload.name}, you said: {payload.message}",
        "original_payload": payload.model_dump(),
    }


@app.post("/users/{user_id}/withdraw")
def withdraw_amount(user_id: str, payload: WithdrawRequest) -> dict:
    balance = bank_balance.get(user_id)
    if balance is None:
        raise HTTPException(status_code=404, detail="User not found")
    if balance < payload.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    bank_balance[user_id] = balance - payload.amount
    return {
        "user_id": user_id,
        "withdrawn": payload.amount,
        "remaining_balance": bank_balance[user_id],
    }


if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
