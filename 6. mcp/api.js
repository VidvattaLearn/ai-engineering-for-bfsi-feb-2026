const express = require("express");

const app = express();
const PORT = 8000;

app.use(express.json());

const bankBalance = {
  "8": 10000,
  "9": 6500,
};

app.get("/", (req, res) => {
  res.json({
    message: "Express demo API is running",
    available_endpoints: [
      "GET /",
      "GET /health",
      "GET /users/:userId/balance",
      "POST /add",
      "POST /echo",
      "POST /users/:userId/withdraw",
    ],
  });
});

app.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

app.get("/users/:userId/balance", (req, res) => {
  const { userId } = req.params;
  const balance = bankBalance[userId];

  if (balance === undefined) {
    return res.status(404).json({ detail: "User not found" });
  }

  return res.json({
    user_id: userId,
    balance,
  });
});

app.post("/add", (req, res) => {
  const { a, b } = req.body;

  if (typeof a !== "number" || typeof b !== "number") {
    return res.status(400).json({
      detail: "Both 'a' and 'b' must be numbers",
    });
  }

  return res.json({
    a,
    b,
    result: a + b,
  });
});

app.post("/echo", (req, res) => {
  const { name, message } = req.body;

  if (!name || !message) {
    return res.status(400).json({
      detail: "Both 'name' and 'message' are required",
    });
  }

  return res.json({
    reply: `Hello ${name}, you said: ${message}`,
    original_payload: req.body,
  });
});

app.post("/users/:userId/withdraw", (req, res) => {
  const { userId } = req.params;
  const { amount } = req.body;
  const balance = bankBalance[userId];

  if (balance === undefined) {
    return res.status(404).json({ detail: "User not found" });
  }

  if (typeof amount !== "number" || amount <= 0) {
    return res.status(400).json({ detail: "Amount must be a positive number" });
  }

  if (balance < amount) {
    return res.status(400).json({ detail: "Insufficient balance" });
  }

  bankBalance[userId] = balance - amount;

  return res.json({
    user_id: userId,
    withdrawn: amount,
    remaining_balance: bankBalance[userId],
  });
});

app.listen(PORT, () => {
  console.log(`Express demo API running on http://127.0.0.1:${PORT}`);
});
