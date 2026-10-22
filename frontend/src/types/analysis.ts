/**
 * Hand-mirrored from backend/app/schemas.py.
 *
 * There is no code generation here on purpose: the mirror is small, and
 * writing it by hand forces a human to notice when the contract changes.
 * RULE: when schemas.py changes, update this file in the same step.
 *
 * Mirrors schema_version "1.0".
 */

/** The four verdicts. "Likely Safe" never means guaranteed safe. */
export type Category =
  | "Likely Safe"
  | "Suspicious"
  | "High Risk"
  | "Unable to Verify";

export type Severity = "info" | "low" | "medium" | "high";

export type DetectorName =
  | "rules"
  | "patterns_in"
  | "url_heuristics"
  | "url_reputation"
  | "ml";

/** No "clean" value: an unreported URL is not a verified-safe URL. */
export type ReputationVerdict =
  | "malicious"
  | "suspicious"
  | "not_listed"
  | "unavailable";

export type ReputationProvider = "google_safe_browsing" | "virustotal";

/** Character offsets into the submitted message. */
export interface EvidenceSpan {
  start: number;
  end: number;
  quote: string;
}

export interface WarningSign {
  code: string;
  title: string;
  description: string;
  severity: Severity;
  detector: DetectorName;
  evidence: EvidenceSpan[];
}

export interface ReputationResult {
  provider: ReputationProvider;
  /** ISO-8601 string; Pydantic serialises datetime this way. */
  checked_at: string | null;
  verdict: ReputationVerdict;
  detail: string | null;
}

/**
 * A URL found in the message.
 *
 * UI RULE: render these as plain text only. Never an <a href>, never
 * dangerouslySetInnerHTML. The user must not be one click from the scam.
 */
export interface ExtractedUrl {
  raw: string;
  normalized: string | null;
  scheme: string | null;
  host: string | null;
  registrable_domain: string | null;
  path: string | null;

  is_ip_host: boolean;
  is_shortener: boolean;
  is_punycode: boolean;
  /** HTTPS is not proof of legitimacy. Do not render this as a green tick. */
  uses_https: boolean;

  heuristic_flags: string[];
  reputation: ReputationResult[];
  assessment: Category;
}

export interface CheckRecord {
  name: string;
  detail: string | null;
}

export interface AnalysisResponse {
  schema_version: string;
  request_id: string;
  analyzed_at: string;

  category: Category;

  /** null when no active method justifies a number. Render the absence. */
  score: number | null;
  score_basis: string | null;

  warning_signs: WarningSign[];
  extracted_urls: ExtractedUrl[];

  checks_performed: CheckRecord[];
  /** Must be shown to the user. A check that did not run is not a pass. */
  checks_failed: CheckRecord[];

  reasons: string[];
  recommended_next_steps: string[];
  disclaimer: string;
}

export interface AnalyzeRequest {
  message: string;
  /** Opt-in, default false: sends URLs to a third party. */
  allow_reputation_lookup: boolean;
}
