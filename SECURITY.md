# Security

This is a paper-only demonstration, **not** a secure production trading system.

- Never commit .env, broker credentials, API tokens or wallet seed phrases.
- Use independent high-entropy TM_API_KEY and TM_WEBHOOK_SECRET secrets (at least 16 characters each).
- Keep the service bound to localhost; use HTTPS and hardening before remotely exposing a webhook.
- Webhook price is caller-supplied and not verified against an exchange. No fees, spreads, latency, order failures or slippage are simulated.
- There is no live trading, leverage or shorting. Cash and symbol notional limits are basic safety checks, not comprehensive risk management.
- If deployed beyond localhost, add rate limiting, proper secret storage, request freshness checks, observability, and a security review.
