# ScamShield India — Architecture (Milestone 1)

Educational prototype. Not affiliated with any bank, company or government
agency. Automated detection can make mistakes.

## 1. The one rule everything follows

**Detectors produce evidence. One scorer decides. Narrators only explain.**

| Role | Modules | May decide a verdict? |
|---|---|---|
| Evidence producer | `detectors/rules.py`, `detectors/patterns_in.py`, `urlcheck/heuristics.py`, `urlcheck/reputation.py`, `detectors/ml.py` | **No** |
| Decider | `scoring.py` | **Yes — the only one** |
| Narrator (optional, M9) | an LLM | **No.** Rewords findings only |

Consequences, which are the point of the design:

- **Explainability is free.** The warning signs shown to the user *are* the
  findings. No reason is ever reconstructed after the fact.
- **Partial failure is survivable.** A detector that cannot run contributes
  no findings and records itself in `checks_failed`. The response says so.
- **Each detector is a pure function** — text in, findings out — so it is
  unit-testable with no network and no fixtures.
- **Prompt injection cannot reach the decision.** The SMS is attacker-
  controlled text. An LLM that may only reword deterministic findings cannot
  be talked into changing the verdict.

## 2. Data flow

```
browser (textarea)
  │  POST /api/v1/analyze  { message, allow_reputation_lookup:false }
  │  CORS allow-list · body-size limit · rate limit
  ▼
routers/analyze.py  ──  Pydantic AnalyzeRequest validates (<= 2000 chars)
  │
  ├─> detectors/rules.py        ─┐
  ├─> detectors/patterns_in.py   │
  ├─> urlcheck: extract → normalize → heuristics  (offline, never fetches)
  │        └─> urlcheck/reputation.py  (only if allow_reputation_lookup)
  └─> detectors/ml.py (M8)      ─┘
  │
  │  list[Finding] + list[CheckOutcome]
  ▼
scoring.py            ──  category, optional score, reasons
  ▼
AnalysisResponse      ──  always the same shape
  ▼
React: rendered as PLAIN TEXT. URLs are never clickable.
```

Findings flow one way only. No detector reads another detector's output, so
no single noisy rule can amplify itself.

## 3. Contracts

| Contract | File | Scope |
|---|---|---|
| `Finding`, `CheckOutcome`, `Detector` | `backend/app/detectors/base.py` | internal |
| `AnalyzeRequest`, `AnalysisResponse` | `backend/app/schemas.py` | public API |
| TypeScript mirror | `frontend/src/types/analysis.ts` | public API |

The internal and public shapes are deliberately separate: evidence can be
refactored without breaking the frontend.

`schemas.py` and `analysis.ts` are mirrored **by hand**. Change one, change
the other in the same step.

## 4. Four categories

`Likely Safe` · `Suspicious` · `High Risk` · `Unable to Verify`

- "Likely Safe" never means guaranteed safe.
- "Unable to Verify" is a real answer, not an error state.
- Mentioning a bank, UPI or KYC **alone** never makes a message fraudulent.
- An unreported URL is not a verified-safe URL — hence no `clean` verdict in
  `ReputationVerdict`, only `not_listed`.
- HTTPS is not proof of legitimacy.

## 5. Honesty invariants

1. `score` is `null` unless the active methods justify a number.
   `score_basis` always says which methods ran, or why there is no score.
2. A check that did not run appears in `checks_failed`. It is never treated
   as a pass and never hidden.
3. `confidence` on a Finding means "how sure the detector is that it
   observed this", never "how likely this is a scam".
4. No metric is ever reported before `ml/evaluate.py` has produced it.

## 6. Security boundaries

| Boundary | Rule | Milestone |
|---|---|---|
| URL handling | never fetch, follow or resolve a URL from an SMS | 6 |
| Reputation API | opt-in with informed consent; failure → `Unable to Verify` | 7 |
| Secrets | backend env vars only, never in frontend code | 2 |
| CORS | explicit origin allow-list, never `["*"]` | 2 |
| Input | server-side validation, 2000-char cap, rate limit | 4, 10 |
| Rendering | plain text only; no `dangerouslySetInnerHTML`; links not clickable | 3 |
| Logging | never log raw SMS, phone numbers or extracted URLs | 10 |
| Storage | none server-side; history in browser `localStorage`, clearable | 3 |

## 7. Folder map

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

`data/` and `artifacts/` are gitignored. Every stub module names the
milestone that will implement it.
