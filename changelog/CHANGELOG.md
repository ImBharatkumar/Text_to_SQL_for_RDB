# Changelog

---

## 24/06/26 (2)

### Fix render domain tabs dynamically from a new /api/domains endpoint

**File changed:**
- `main.py` — added `GET /api/domains`, which scans `DOMAINS_DIR` and returns `{domains: [{name, description, table_count}]}` (sorted by filename)
- `static/index.html` — emptied `.domain-selector` (now `id="domain-selector"`); tabs are injected by JS instead of being hardcoded
- `static/app.js` — replaced the static `.domain-tab` NodeList wiring with `loadDomainTabs()` / `renderDomainTabs()`; added a `DOMAIN_ICONS` map (with `fa-database` fallback); `currentDomain` now starts `null` and is set to the first returned domain; init calls `loadDomainTabs()` instead of `loadDomainConfig('healthcare_claims')`

**Problem:** Domain tabs were hardcoded in `index.html`, so every new domain YAML required a manual HTML edit (the exact drift that left 5 domains invisible in the prior fix). There was also no API to enumerate domains.

**Fix:** `GET /api/domains` enumerates the `domains/` directory server-side. On load, `app.js` fetches it and builds one `.domain-tab` button per domain — wiring the same click→`loadDomainConfig` behavior, applying a per-domain FontAwesome icon (fallback `fa-database`), activating the first domain, and loading its config. Adding a YAML now surfaces a tab automatically with no frontend change. Note: the default-selected domain is now the first alphabetically (`ecommerce`) rather than `healthcare_claims`.

**Revert:** In `main.py`, delete the `list_domains` function and its `@app.get("/api/domains")` decorator. In `static/index.html`, restore the hardcoded `<button class="domain-tab" ...>` entries inside `.domain-selector` (and drop the `id`). In `static/app.js`, restore `const domainTabs = document.querySelectorAll('.domain-tab');`, `let currentDomain = 'healthcare_claims';`, the original `domainTabs.forEach` switch block, and the init call `loadDomainConfig(currentDomain);`; remove `DOMAIN_ICONS`, `domainIcon`, `domainSelector`, `loadDomainTabs`, and `renderDomainTabs`.

---

## 24/06/26

### Fix sync semantic_model defaults and frontend tabs with all 7 domains

**File changed:**
- `semantic_model.py` — added `ecommerce`, `finance_banking`, `logistics`, `hr_payroll`, and `education` to `DEFAULT_DOMAINS` (previously only `healthcare_claims` and `retail_sales`)
- `static/index.html` — added five `.domain-tab` buttons (ecommerce, finance_banking, logistics, hr_payroll, education) to the `.domain-selector` so all seven domains are selectable

**Problem:** Five new domain YAMLs (`ecommerce`, `finance_banking`, `logistics`, `hr_payroll`, `education`) had been added to `domains/`, but `DEFAULT_DOMAINS` in `semantic_model.py` still seeded only the original two. The frontend `domain-selector` likewise hardcoded only `healthcare_claims` and `retail_sales`, so users could not view or edit the five new domains in the UI even though the backend indexed them (it scans `domains/` via `os.listdir`).

**Fix:** Mirrored each new YAML's tables/columns into `DEFAULT_DOMAINS` so the in-code seed matches what is on disk (verified: `DEFAULT_DOMAINS` keys are all 7 domains). Added a `domain-tab` button for each new domain in `index.html`; the existing `app.js` tab handler reads `data-domain` and calls `loadDomainConfig`, so no JS change was needed.

**Revert:** In `semantic_model.py`, delete the `ecommerce`, `finance_banking`, `logistics`, `hr_payroll`, and `education` keys from `DEFAULT_DOMAINS`, leaving the dict closed after the `retail_sales` block. In `static/index.html`, remove the five `<button class="domain-tab" data-domain="...">` entries for ecommerce/finance_banking/logistics/hr_payroll/education from `.domain-selector`.

---

## 23/06/26 (3)

### Fix cross-domain queries failing with "Insufficient context"

**File changed:**
- `main.py` — in `/api/query`, raised retriever `top_k` from 2 to 8 and expanded the retrieved set to every table in any matched domain (both for the LLM schema context and the validation whitelist); added context fallback when retrieval is empty
- `validator.py` — expanded `DEFAULT_WHITELIST_TABLES` from 5 tables to all 31 seeded tables across the 7 domains

**Problem:** Natural-language questions that required more than two tables (e.g. an hr_payroll question needing `departments` + `employees` + `salaries` + `performance_reviews`) returned `ERROR: Insufficient context`. `retriever.retrieve(question, top_k=2)` handed the LLM only the two highest-scoring tables, and rule #4 of the prompt makes it emit that error when it cannot answer from the given schema. The per-query whitelist (`retrieved_tables`) was also limited to those two tables, so any wider join would have been rejected by `validate_sql` anyway.

**Fix:** `top_k` is now 8 to widen the candidate net, and after retrieval the set is expanded to all tables sharing a matched domain (`expanded = [e for e in retriever.index if e["domain"] in matched_domains]`). Both `retrieved_context` (LLM schema) and `retrieved_tables` (validation whitelist) are derived from this expanded set, so multi-table and cross-domain joins now have the context and whitelist to succeed. `DEFAULT_WHITELIST_TABLES` was also broadened so direct callers of `validate_sql` aren't capped at the original 5 tables.

**Revert:** In `main.py` `/api/query`, restore `top_matches = retriever.retrieve(question, top_k=2)`, set `retrieved_context = "\n\n".join([m["text"] for m in top_matches])` and `retrieved_tables = {m["table"].lower() for m in top_matches}`, and delete the `matched_domains`/`expanded` lines and the context line added to the empty-retrieval fallback. In `validator.py`, restore `DEFAULT_WHITELIST_TABLES = {"claims", "payments", "payers", "members", "sales"}`.

---

## 23/06/26 (2)

### Fix load Gemini key from .env and remove mock SQL fallback

**File changed:**
- `main.py` — call `load_dotenv()` at startup; deleted `generate_mock_sql`; `/api/query` now requires `GEMINI_API_KEY` (HTTP 500 if missing/placeholder, HTTP 502 on Gemini error) with no fallback
- `pyproject.toml` / `requirements.txt` — added `python-dotenv` dependency
- `.env` / `.env.example` — new files holding `GEMINI_API_KEY`
- `.gitignore` — new file; ignores `.env`, caches, venv, local db
- `README.md` — setup now describes `.env`; removed mock-mode wording
- `test_api.py` / `test_pipeline.py` — `/api/query` tests are key-aware (expect 500 with no key, 200/502 with a key); fixed `test_api.py` route paths to include `/api` prefix

**Problem:** The Gemini key was only read from the raw process environment (`os.environ.get`), so it had to be exported manually each shell session. When Gemini returned 503, the code silently fell back to `generate_mock_sql`, which produced a generic query that then failed the per-query table whitelist ("Executed SQL fallback check: Denied") — a confusing double failure.

**Fix:** Added `python-dotenv` and `load_dotenv()` so the key loads from `.env` automatically. Removed the mock generator entirely; `/api/query` now raises HTTP 500 when the key is absent/placeholder and HTTP 502 when the Gemini call fails, surfacing the real cause instead of a denied mock query. `genai.Client(api_key=api_key)` now receives the key explicitly.

**Revert:** In `main.py`, remove the `from dotenv import load_dotenv` import and the `load_dotenv()` call; restore the `generate_mock_sql` function and the original `if api_key: ... else: ...` block that fell back to it; change `genai.Client(api_key=api_key)` back to `genai.Client()`; restore `"validation_error": validation_error or warning_msg`. Remove `python-dotenv` from `pyproject.toml`/`requirements.txt`. Delete `.env`, `.env.example`, `.gitignore`. Revert the test files and README section.

---

### Fix frontend never loading its CSS or JavaScript

**File changed:**
- `static/index.html` — corrected stylesheet path to `/static/index.css` and added the missing `<script src="/static/app.js">` tag

**Problem:** The dashboard rendered unstyled and completely inert — no domain config loaded, suggestion/query buttons did nothing, no pipeline output. Two causes: (1) `app.js` was never referenced by any `<script>` tag, so none of the frontend logic ran; (2) the page is served from `/` (FileResponse in `main.py`) while static assets are mounted at `/static/`, so the relative `href="index.css"` resolved to `/index.css` and 404'd.

**Fix:** Changed `<link rel="stylesheet" href="index.css">` to `href="/static/index.css"` and added `<script src="/static/app.js"></script>` just before `</body>`. Both assets now resolve against the `/static/` mount, so the CSS loads and `app.js` executes (wiring up event handlers and the initial `loadDomainConfig` call).

**Revert:** In `static/index.html`, change `href="/static/index.css"` back to `href="index.css"`, and delete the `<script src="/static/app.js"></script>` line (with its `<!-- Application Logic -->` comment) near the end of `<body>`.

---
