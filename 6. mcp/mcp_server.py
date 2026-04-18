from fastmcp import FastMCP
import random

mcp = FastMCP("Demo 🚀")

@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool
def get_secret_word() -> str:
    """Tool to get a secret word"""
    words = ["apple", "banana", "cherry", "date", "elderberry"]
    return random.choice(words)

bank_balance = {
  "8": 10000,
  "9": 6500
}

@mcp.tool
def get_bank_balance(user_id: str):
  """Tool providing bank balance of user"""
  balance = bank_balance.get(user_id)
  return f"Bank balance is {balance}"

@mcp.tool
def withdraw_amount(amount: int, user_id: str):
  """Tool to withdraw given amount"""
  balance = bank_balance.get(user_id)
  if balance >= amount:
    bank_balance[user_id] = balance - amount
    return f"Withdrawn {amount}. Remaining balance is {bank_balance[user_id]}"
  else:
    return "Insufficient balance"

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=9000)