# TradeMesh AI

**Open-source multi-broker trading automation platform — in development.**

![Status](https://img.shields.io/badge/status-v0.1%20paper%20MVP-blue)
![Execution](https://img.shields.io/badge/execution-PAPER%20ONLY-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

**Current working release (v0.1):** a lightweight Python/FastAPI TradingView-style webhook receiver, basic risk checks, SQLite-backed simulated portfolio and automated API tests. This release **does not connect to brokers or exchanges or place live trades**. It is an educational paper-only prototype.

## What works

- HTTP JSON webhook receiver (compatible with TradingView-style alerts)
- Simulated **long-only spot** orders for `BTCUSDT`, `ETHUSDT`, `SOLUSDT`
- Duplicate signal ID prevention, atomic SQLite writes and persistent portfolio
- Basic cash, maximum order notional ($2,000) and symbol exposure ($3,000) limits
- Protected portfolio endpoint with an API key
- Example payload, Docker Compose, test suite and implementation roadmap

## Local setup (Python 3.11+)

```bash
git clone https://github.com/rajachanna/TradeMesh-AI.git
cd TradeMesh-AI
python -m venv .venv
# macOS/Linux: source .venv/bin/activate
# Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` to replace both placeholder secrets with **different random values at least 16 characters long**. Set both in your shell before starting the app (the application does not automatically load .env):

```bash
# macOS/Linux
set -a; source .env; set +a
uvicorn trademesh.api:app --app-dir src --host 127.0.0.1 --port 8000
```

On Windows, set `TM_API_KEY` and `TM_WEBHOOK_SECRET` as environment variables through PowerShell before running uvicorn.

API documentation: **http://127.0.0.1:8000/docs** · Health: **http://127.0.0.1:8000/health**

### Docker

```bash
cp .env.example .env
# edit .env secrets
docker compose up --build
```

Docker binds port 8000 to localhost only and persists the paper SQLite database in a Docker volume.

## Test a simulated alert

```bash
curl -X POST http://127.0.0.1:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"secret":"YOUR_TM_WEBHOOK_SECRET","id":"unique-signal-001","symbol":"BTCUSDT","side":"buy","quantity":0.01,"price":65000}'
```

Each new intended order needs a different `id`. Repeated IDs return `duplicate` and do not execute a second simulated trade.

```bash
curl -H "X-API-Key: YOUR_TM_API_KEY" http://127.0.0.1:8000/portfolio
```

The simulated starting cash is **$10,000 USD**. Alerts supply the fill price: it is **not independently verified**, so this is not valid backtesting or evidence of profitability. There is no fee, spread, slippage, market-liquidity, fill-failure, latency, P&L analytics, or live market-data model.

### Run tests

```bash
pip install -r requirements-dev.txt
PYTHONPATH=src pytest -q
```

For Windows PowerShell, run `$env:PYTHONPATH="src"; pytest -q`.

## API

| Route | Authentication | Purpose |
| --- | --- | --- |
| `GET /health` | None | Paper-mode health |
| `POST /webhook` | Secret in JSON body | Submit simulated order |
| `GET /portfolio` | `X-API-Key` request header | Read simulated account |

## Planned integrations — **not yet implemented**

- Interactive Brokers (IBKR) paper account adapter
- MetaTrader 5 demo account adapter
- Crypto CEX testnet/sandbox connectors and DEX simulation
- TradingView signal freshness, signature support, rate limits
- Portfolio dashboard, strategy backtesting, risk analytics, AI explanations
- Proper production-grade risk controls and broker reconciliation

See [ROADMAP.md](ROADMAP.md) and [SECURITY.md](SECURITY.md) for details and limitations.

## Project and consulting

Developed by **NextGen Tech Solutions** · https://nextgentechdev.com

MIT licensed. Contributions and issues are welcome.

> **Disclaimer:** This is an experimental software prototype, not financial advice. Automated trading is risky and no strategy is guaranteed to make a profit. Do not expose this MVP directly to the public internet without a security review.
