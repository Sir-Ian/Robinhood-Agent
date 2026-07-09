# Security Policy

This repository is intentionally public. Do not open a public issue containing brokerage account numbers, authentication material, raw broker payloads, order-review disclosures tied to a private account, or other sensitive financial information.

If you find a credential or sensitive identifier in the repository, contact the repository owner privately and include only the file path and commit hash. Do not copy the secret into the report.

The automated public-safety check is a defense-in-depth control, not a guarantee. Before every publication, run `make validate` and inspect the staged diff.
