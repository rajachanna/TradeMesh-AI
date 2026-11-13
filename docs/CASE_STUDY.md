# TradeMesh AI — Engineering case study

**Author:** Raja Channa · NextGen Tech Solutions  
**Stage:** v0.1 experimental prototype · **Mode:** Paper only · **Source:** [TradeMesh AI repository](../README.md)

## Executive overview

TradeMesh AI investigates a practical question in trading automation:

> How do you take a strategy signal, apply basic operational checks, simulate execution, and preserve enough state to explain what happened?

The v0.1 deliverable is a small FastAPI service backed by SQLite, plus a local read-only portfolio dashboard and Python API tests. It intentionally **does not** connect to a brokerage account, exchange, live market data feed or wallet.

This is an engineering sample rather than evidence of a profitable trading strategy.

## Product challenge

In multi-system trading workflows, several risks appear before any strategy logic is considered:

1. A webhook may be resent, causing an unintended second order.
2. A signal may ask for a position larger than available cash.
3. The current portfolio may be inconsistent with the latest event.
4. A monitoring screen may expose sensitive account information to an unauthenticated request.
5. A demo may be marketed as if simulated fills were real exchange transactions.

The first release provides narrow, inspectable answers to some of these risks.

## Decisions and trade-offs

| Choice | Rationale | Limitation |
| --- | --- | --- |
| Paper-only mode | Separates interface/risk development from funded capital | Cannot prove exchange execution quality |
| Python + FastAPI | Clear API contracts and input validation | Not a low-latency exchange execution engine |
| SQLite transactions | Small local demo with atomic account/order writes | Not an HA/distributed broker ledger |
| Distinct webhook and portfolio secrets | Separates alert submission from account viewing | Not enterprise authentication or rate limiting |
| Caller-supplied prices | Makes demo deterministic and easy to reproduce | No independent price verification; unsuitable for performance analysis |
| Long-only spot simulation | Restricts the state model and avoids leverage complexities | No shorts, derivatives, margin or real broker fills |
| Duplicate order IDs | Demonstrates one practical idempotency boundary | No distributed replay-protection system; a different ID can represent the same strategy event |

## Walk through an example

**Given:** The local demo starts with $10,000 in simulated USD cash.

**When:** An authorized \`BTCUSDT\` buy alert with quantity \`0.01\` and price \`65000\` is received.

**Then:** The prototype debits $650 from simulated cash and records the position and order.

**When:** The exact same alert ID is submitted again.

**Then:** The service returns \`duplicate\` and does not apply a second fill.

**When:** A separate sell alert closes the owned quantity at an **invented example price** of \`66000\`.

**Then:** The demo account has $10,010 in cash, ignoring all real-world costs and execution differences.

This demonstrates state bookkeeping and duplicate suppression, **not** a real trade or returns forecast.

## API and code to inspect

- [Signal validation, simulated fills and risk checks](../src/trademesh/api.py)
- [Read-only dashboard implementation](../src/trademesh/static/index.html)
- [Regression tests and negative cases](../tests/test_api.py)
- [Example alert](../examples/tradingview-alert.json)

**Evaluation checklist for a technical client:**

- [ ] Clone and run locally using the [README instructions](../README.md#quick-start).
- [ ] Verify the dashboard only returns portfolio data after a valid API key.
- [ ] Submit a buy alert, then repeat the ID and confirm no second fill.
- [ ] Try an unsupported symbol, an oversize order, and a sell with no holdings.
- [ ] Run the test suite and review the results yourself.
- [ ] Compare actual needs with the **not-yet-implemented** broker features below.

The boxes above describe actions for the reviewer; they are not a certification that an independent auditor completed them.

## What needs to happen before a real broker integration

| Engineering gate | Work needed |
| --- | --- |
| Broker interface | Typed adapter contract, account/contract validation, order lifecycle |
| Safe market data | Trusted quote source, quote age and symbol mapping |
| Full risk engine | Daily drawdown, gross exposure, account-level limits, kill switch |
| Reliable execution | Retries, idempotency across instances, reconciliation and incident recovery |
| Security | Secrets manager, TLS, request replay controls, rate limits, audit logs |
| Trading realism | Fees, spreads, slippage, partial fills, funding and liquidity assumptions |
| Delivery evidence | Broker sandbox runs, measured acceptance tests, reproducible reports |

**Do not connect the v0.1 webhook directly to a funded account.**

## Collaboration model

For client work, the recommended scope is an independently testable milestone:

1. **Discovery:** supported broker, trading instruments, rules, environment and risk limits.
2. **Prototype:** paper/demo adapter and repeatable example signals.
3. **Verification:** negative cases, execution acknowledgement and client acceptance evidence.
4. **Optional production hardening:** only after a separate risk and security review.

### Relevant services

Custom MT5 and IBKR workflows, TradingView signal bridges, CEX sandbox integrations, broker API troubleshooting and trading dashboard/reporting automation.

**Discuss a scoped integration:** https://nextgentechdev.com

---

*This repository is a technical showcase. It does not demonstrate actual exchange profitability, compliance certification, live fill performance or investment returns.*
