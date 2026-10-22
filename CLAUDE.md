# ScamShield India

Web app: a user pastes an SMS and gets an explainable scam-risk assessment.
Educational prototype. Never claim affiliation with any government agency.

## How to work with me
I'm an engineering student, new to React, interested in AI/ML. TEACH me.
Work ONE milestone at a time. For each: explain the goal in plain language,
the concepts and architecture, the dependencies, the exact commands, then
create the files and explain the important code. Tell me how to run it, give
a test case with expected output, and explain the security risks and
trade-offs. Never skip ahead. Don't assume any API key, dataset or service
is configured. Wait for me after each milestone.

## Environment
macOS, Node 26, npm 11. Python 3.13 at /opt/homebrew/bin/python3.13
(bare `python3` is Apple's 3.9: always create venvs with the 3.13 path).

## Stack
- Frontend: React, Vite, TypeScript, Tailwind (added at Milestone 3),
  accessible components, Vitest + Testing Library.
- Backend: Python, FastAPI, Pydantic, pytest.
- ML: scikit-learn, TF-IDF + logistic regression baseline.
- Storage: none. Scan history in browser localStorage only, with a clear
  button. Do not save raw SMS by default.

## Core architecture rule
Every detector is an EVIDENCE PRODUCER that emits Findings (rules, URL
heuristics, reputation lookup, later the ML model). A separate scoring step
turns findings into a score and category. Narrators (any future LLM) may only
explain findings, never create or decide them.

Response JSON always includes: category, score (only if the method justifies
it), warning signs, extracted URLs, URL reputation results, checks_performed,
checks_failed, reasons, recommended next steps, and a statement that automated
detection can make mistakes.

## Categories
Likely Safe, Suspicious, High Risk, Unable to Verify.
"Likely Safe" never means guaranteed safe. Mentioning a bank, UPI or KYC
alone must never make a message fraudulent. An unreported URL is not a
verified-safe URL. HTTPS is not proof of legitimacy.

## URL safety (non-negotiable)
- Never open links in the user's browser. Never fetch, follow redirects from,
  or download anything from a URL found in an SMS on the backend.
- V1 = offline URL parsing/heuristics + optional reputation APIs (Google Safe
  Browsing; VirusTotal free tier is rate-limited and non-commercial).
  Heuristics: shorteners, lookalike domains, IP-address hosts, odd subdomains,
  punycode, suspicious patterns.
- Reputation lookups send a URL to a third party: make them opt-in with
  informed consent. If unconfigured or failed, record it in checks_failed
  and return "Unable to Verify" for that URL.
- API keys only in backend env vars, never in frontend code.
- Any future deep inspection must be an isolated, disposable service with
  strict network limits. Not in V1.

## Privacy and security
Server-side validation, request-size limits, rate limiting, safe error
messages, minimal logging (never log raw SMS), no collection of phone numbers
or financial details, prompt-injection resistance (SMS text is attacker
input), a clear privacy notice. The app never asks users for OTPs,
passwords, UPI PINs or banking details.

## React-specific rules
- Configure CORS with an explicit allow-list of origins (local dev origin
  plus the deployed frontend). Never use allow_origins=["*"].
- Never use dangerouslySetInnerHTML. SMS text is attacker input and must be
  rendered as plain text.
- Keep frontend/src/types/analysis.ts hand-mirrored with backend schemas.py;
  when one changes, update the other in the same step.
- API base URL comes from a Vite env var (VITE_API_URL), never hardcoded.
- Always handle loading, error, timeout and "backend unreachable" states.
- Pin dependency versions. Node 26 is very new: if a package fails to
  install, tell me and check compatibility before changing versions.
- Deployment note: free backend tiers sleep when idle. Plan a warm-up
  step before any demo.

## India-specific coverage
UPI/collect-request fraud, fake bank KYC and suspension, fake courier/parcel,
electricity disconnection, government-benefit/subsidy impersonation, fake
jobs/work-from-home, investment/trading scams, fake customer-care numbers,
digital-arrest impersonation, phishing links imitating Indian services.
English first; plan Hindi and other Indian languages for later. Before
showing CERT-In / National Cyber Crime Reporting Portal / 1930 helpline
guidance, verify it is current.

## UI
Dark navy, white, subtle teal. Responsive and accessible. Sections: Home;
SMS analyzer (large textarea, character counter, Clear, Analyze); safe
example messages; results (risk indicator, explanation, suspicious phrases,
link analysis); safety recommendations; recent scans (local, clearable);
About (how it works, limitations, privacy).

## ML honesty
Never invent accuracy or claim a model is trained when it isn't. Report
precision, recall and F1 on the scam class, not accuracy (UCI is ~87% ham, so
"always ham" already scores 86.6%). Explain false positives/negatives and
class imbalance. Datasets: Mendeley f45bkkt8pr (CC BY 4.0, 3-class) as
primary; UCI SMS Spam Collection as baseline; SmishTank (CC BY-NC-SA) for
testing only. None of them are Indian: say so in the report. Synthetic data
must be labelled and never used in the test set.

## Folder structure
backend/app/{main,config,schemas,scoring,logging_conf}.py
backend/app/routers/analyze.py
backend/app/detectors/{base,rules,patterns_in,ml}.py
backend/app/urlcheck/{extract,normalize,heuristics,reputation}.py
backend/ml/{train,evaluate}.py, data/ (gitignored), artifacts/
backend/tests/   frontend/src/{api,types,components,lib,pages}/

## Roadmap (in order)
Suggested sequencing: finish the backend (schema, API stub, detectors,
URL analysis) before building the React UI, so the frontend is built
against a working API.
1. Architecture, data flow, folder structure, and the AnalysisResponse schema.
2. Dev environment; backend venv + minimal FastAPI health endpoint; Vite
   React TS app. Skip Tailwind until 3.
3. SMS input UI and responsive dashboard (add Tailwind here).
4. FastAPI /api/v1/analyze with Pydantic validation; connect the frontend.
5. Rule-based SMS detector (transparent baseline, India patterns).
6. Safe URL parsing and suspicious-domain analysis (no fetching).
7. Optional threat-intelligence API integration, securely.
8. Dataset audit, then train and evaluate the TF-IDF baseline; compare with
   the rule-based approach (precision/recall/F1, confusion matrix).
   Optional: Gemma LoRA comparison arm in Colab.
9. Fuse text classifier + URL evidence into an explainable risk assessment.
   Optional LLM narrator (explains findings only; can add Hindi).
10. Tests (pytest + frontend), error handling, privacy controls, security
    checks (SSRF, rate limits, input limits).
11. Deploy (frontend + backend) and prepare a demo.
12. Project report: architecture diagram, dataset explanation, metrics,
    limitations, viva questions.

Final goal: a functioning educational prototype with real SMS analysis and
safe link-reputation checks, not a static UI or a chatbot that guesses.
