# Public Data And Privacy Boundary

The purpose of this repository is transparency, so sanitized investment facts may be public. Authentication and account-identifying data may not.

## Allowed Public Data

- Account alias, never account number.
- Rounded portfolio value, cash, buying power, positions, quantities, prices, and weights.
- Symbols, sides, dollar amounts, fill quantities, fill prices, and timestamps.
- Stable local execution IDs and idempotency keys that reveal no broker identifier.
- Policies, prompts, run outcomes, incidents, reconciliations, benchmark results, and strategy proposals.
- Explicitly labeled broker-confirmed, computed, paper, imported, and unavailable evidence.

## Forbidden Public Data

- Brokerage, RHS, or crypto account numbers.
- Broker order UUIDs, when a local public reference is sufficient.
- Tokens, cookies, session IDs, authorization headers, API keys, or credentials.
- Raw broker/MCP responses or tool `guide` payloads.
- Full private logs, browser state, or screenshots containing account UI.
- Personal addresses, tax details, legal names not already intentionally public, or unrelated account holdings.

## Publication Rule

Public files are a curated audit layer, not a raw event dump. Store raw/private material only outside the repository or under ignored paths. Run `make validate` before every publication and treat a scan failure as blocking.
