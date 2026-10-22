# ScamShield India

Paste an SMS, get an **explainable** scam-risk assessment: not just a verdict,
but the exact phrases and link properties that produced it.

> **Educational prototype.** Not affiliated with any bank, company or
> government agency. Automated detection can make mistakes, and "Likely Safe"
> never means guaranteed safe.

---

## Status

**Milestone 1 of 12 complete** — architecture, folder skeleton and the API
contract. There is **no runnable app yet**: `backend/app/main.py` and every
detector are documented stubs that name the milestone which will implement
them. No model is trained. No accuracy figures exist, so none are quoted
anywhere in this repo.

| # | Milestone | State |
|---|---|---|
| 1 | Architecture, folder structure, `AnalysisResponse` schema | ✅ done |
| 2 | Dev environment, venv, FastAPI health endpoint, Vite app | ⬜ next |
| 3 | SMS input UI and responsive dashboard (Tailwind) | ⬜ |
| 4 | `POST /api/v1/analyze` with Pydantic validation, wired to UI | ⬜ |
| 5 | Rule-based detector + India-specific patterns, and the scorer | ⬜ |
| 6 | Offline URL parsing and suspicious-domain heuristics | ⬜ |
| 7 | Optional threat-intelligence lookups, opt-in | ⬜ |
| 8 | Dataset audit, TF-IDF + logistic-regression baseline, evaluation | ⬜ |
| 9 | Fuse text + URL evidence; optional LLM narrator | ⬜ |
| 10 | Tests, error handling, privacy and security hardening | ⬜ |
| 11 | Deploy frontend + backend, prepare demo | ⬜ |
| 12 | Project report: diagrams, metrics, limitations, viva questions | ⬜ |

## The one design rule

**Detectors produce evidence. One scorer decides. Narrators only explain.**

```
SMS text
  ├─> rules            ─┐
  ├─> patterns_in       │  each emits Findings — factual observations
  ├─> url_heuristics    │  ("this phrase is at characters 41–58"),
  ├─> url_reputation    │  never a verdict
  └─> ml                ─┘
                         │  list[Finding] + list[CheckOutcome]
                         ▼
                      scoring.py   ← the only module that picks a category
                         ▼
                      AnalysisResponse
```

Why it is built this way:

- **Explainability is free.** The warning signs shown to the user *are* the
  findings. No reason is ever reconstructed after the fact.
- **Partial failure is survivable.** A check that cannot run contributes no
  findings and records itself in `checks_failed`. It is never silently
  counted as a pass.
- **Prompt injection cannot reach the decision.** The SMS is attacker-
  controlled text. A future LLM may only reword deterministic findings, so it
  cannot be talked into changing the verdict.
- **Each detector is a pure function** — text in, findings out — so it is
  unit-testable with no network and no fixtures.

Full write-up, including the security boundaries table: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## The four categories

`Likely Safe` · `Suspicious` · `High Risk` · `Unable to Verify`

- "Unable to Verify" is a real answer, not an error state.
- Mentioning a bank, UPI or KYC **alone** never makes a message fraudulent.
- An unreported URL is not a verified-safe URL — hence `not_listed`, never
  `clean`.
- HTTPS is not proof of legitimacy.
- `score` stays `null` until a method justifies a number; `score_basis`
  always says which methods ran, or why there is no score.

## URL safety (non-negotiable)

Links found in an SMS are **never opened**. The backend does not fetch them,
does not follow their redirects, and does not resolve shorteners by
requesting them; the frontend never renders them as clickable. Everything in
`ExtractedUrl` comes from parsing the string offline: shorteners, IP-address
hosts, punycode lookalikes, odd subdomains, suspicious paths.

Third-party reputation lookups transmit a URL to an external provider, so
they are **off by default** and require an explicit per-request opt-in
(`allow_reputation_lookup`). If unconfigured or failed, the lookup lands in
`checks_failed` and that URL comes back as "Unable to Verify". API keys live
in backend environment variables only.

## Privacy

No server-side storage. Scan history lives in browser `localStorage` with a
clear button. Raw SMS text, phone numbers and extracted URLs are never
logged. The app never asks for OTPs, passwords, UPI PINs or banking details.

## Stack

| Layer | Choice |
|---|---|
| Frontend | React, Vite, TypeScript, Tailwind (from M3), Vitest + Testing Library |
| Backend | Python 3.13, FastAPI, Pydantic, pytest |
| ML | scikit-learn, TF-IDF + logistic regression baseline |
| Storage | none — browser `localStorage` only |

Target environment: macOS, Node 26, npm 11, Python 3.13 at
`/opt/homebrew/bin/python3.13` (bare `python3` is Apple's 3.9, so venvs are
always created with the 3.13 path).

## Layout

```
backend/app/{main,config,schemas,scoring,logging_conf}.py
backend/app/routers/analyze.py
backend/app/detectors/{base,rules,patterns_in,ml}.py
backend/app/urlcheck/{extract,normalize,heuristics,reputation}.py
backend/ml/{train,evaluate}.py   backend/data/   backend/artifacts/
backend/tests/
frontend/src/{api,types,components,lib,pages}/
docs/
```

Two contracts matter:

- [backend/app/schemas.py](backend/app/schemas.py) — the public API shape
  (`AnalyzeRequest`, `AnalysisResponse`).
- [frontend/src/types/analysis.ts](frontend/src/types/analysis.ts) — a
  **hand-written** mirror of it. Change one, change the other in the same
  commit.

`backend/app/detectors/base.py` holds the separate *internal* shape
(`Finding`, `CheckOutcome`), so evidence can be refactored without breaking
the frontend. `data/` and `artifacts/` are gitignored.

## Running it

Nothing to run yet — Milestone 2 adds the backend venv, a FastAPI health
endpoint and the Vite app, and this section will carry the exact commands
then.

## Scam types in scope

UPI and collect-request fraud, fake bank KYC / account suspension, fake
courier and parcel notices, electricity disconnection, government-benefit
and subsidy impersonation, fake jobs and work-from-home offers,
investment and trading scams, fake customer-care numbers, digital-arrest
impersonation, and phishing links imitating Indian services. English first;
Hindi and other Indian languages are planned later.

Any CERT-In, National Cyber Crime Reporting Portal or 1930 helpline guidance
shown to users must be re-verified as current before it ships.

## On the ML, honestly

The dataset plan is in [backend/data/README.md](backend/data/README.md):
Mendeley `f45bkkt8pr` (CC BY 4.0) as primary, UCI SMS Spam Collection as a
baseline, SmishTank (CC BY-NC-SA) for testing only. **None of them are Indian
SMS corpora**, which is a real limitation and is stated in the evaluation and
the final report.

Evaluation will report **precision, recall and F1 on the scam class**, not
accuracy: UCI is roughly 87% ham, so a model that always answers "ham"
already scores 86.6% and detects nothing. Synthetic examples, if used, are
labelled as such and never enter the test set.
