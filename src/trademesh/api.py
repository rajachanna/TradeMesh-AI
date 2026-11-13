"""TradeMesh AI: paper-only proof of concept, NOT live trading software."""
from decimal import Decimal
from hmac import compare_digest
from pathlib import Path
import os
import sqlite3

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

app = FastAPI(title="TradeMesh AI — Paper-only prototype", version="0.1.0")
DATABASE = Path(os.environ.get("TM_DB_PATH", "trademesh.db"))


def connect():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE, timeout=30, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=30000")
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE IF NOT EXISTS account(id INTEGER PRIMARY KEY, cash TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS positions(symbol TEXT PRIMARY KEY, qty TEXT NOT NULL, cost TEXT NOT NULL)")
    db.execute("CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, symbol TEXT, side TEXT, quantity TEXT, price TEXT)")
    db.execute("INSERT OR IGNORE INTO account(id,cash) VALUES(1,'10000')")
    return db


class Signal(BaseModel):
    secret: str
    id: str = Field(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9:_-]+$")
    symbol: str = Field(min_length=3, max_length=15, pattern=r"^[A-Za-z0-9]+$")
    side: str
    quantity: Decimal
    price: Decimal

    @field_validator("quantity", "price")
    @classmethod
    def valid_number(cls, v):
        if not v.is_finite() or v <= 0:
            raise ValueError("Must be positive and finite")
        return v


@app.get("/health")
def health():
    return {"mode": "PAPER_ONLY", "ready": True}


@app.post("/webhook")
def webhook(signal: Signal):
    secret = os.environ.get("TM_WEBHOOK_SECRET", "")
    if len(secret) < 16 or not compare_digest(secret, signal.secret):
        raise HTTPException(401, "Invalid webhook secret")
    symbol = signal.symbol.upper()
    if symbol not in {"BTCUSDT", "ETHUSDT", "SOLUSDT"}:
        raise HTTPException(422, "Symbol not allowed")
    if signal.side not in {"buy", "sell"}:
        raise HTTPException(422, "Only buy/sell supported")
    notional = signal.quantity * signal.price
    if notional > Decimal("2000"):
        raise HTTPException(422, "Max order $2000")
    with connect() as db:
        try:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM orders WHERE id=?", (signal.id,)).fetchone():
                db.execute("ROLLBACK")
                return {"status": "duplicate", "mode": "PAPER_ONLY"}
            cash = Decimal(db.execute("SELECT cash FROM account").fetchone()[0])
            row = db.execute("SELECT qty,cost FROM positions WHERE symbol=?", (symbol,)).fetchone()
            qty = Decimal(row["qty"]) if row else Decimal("0")
            avg = Decimal(row["cost"]) if row else Decimal("0")
            if signal.side == "buy":
                if notional > cash or (qty + signal.quantity) * signal.price > Decimal("3000"):
                    raise ValueError("Cash or symbol exposure limit exceeded")
                new_qty = qty + signal.quantity
                new_avg = (qty * avg + notional) / new_qty
                db.execute("INSERT INTO positions VALUES(?,?,?) ON CONFLICT(symbol) DO UPDATE SET qty=excluded.qty,cost=excluded.cost", (symbol, str(new_qty), str(new_avg)))
                cash -= notional
            else:
                if signal.quantity > qty:
                    raise ValueError("Cannot sell more than owned")
                if signal.quantity == qty:
                    db.execute("DELETE FROM positions WHERE symbol=?", (symbol,))
                else:
                    db.execute("UPDATE positions SET qty=? WHERE symbol=?", (str(qty-signal.quantity), symbol))
                cash += notional
            db.execute("UPDATE account SET cash=? WHERE id=1", (str(cash),))
            db.execute("INSERT INTO orders VALUES(?,?,?,?,?)", (signal.id, symbol, signal.side, str(signal.quantity), str(signal.price)))
            db.execute("COMMIT")
        except ValueError as exc:
            db.execute("ROLLBACK")
            raise HTTPException(422, str(exc)) from exc
        except Exception:
            if db.in_transaction:
                db.execute("ROLLBACK")
            raise
    return {"status": "paper_filled", "mode": "PAPER_ONLY", "id": signal.id}


@app.get("/portfolio")
def portfolio(x_api_key: str | None = Header(default=None)):
    key = os.environ.get("TM_API_KEY", "")
    if len(key) < 16 or x_api_key is None or not compare_digest(key, x_api_key):
        raise HTTPException(401, "Invalid API key")
    with connect() as db:
        return {"mode": "PAPER_ONLY", "cash_usd": db.execute("SELECT cash FROM account").fetchone()[0],
                "positions": [dict(r) for r in db.execute("SELECT * FROM positions")],
                "orders": [dict(r) for r in db.execute("SELECT * FROM orders ORDER BY rowid DESC LIMIT 100")]}
