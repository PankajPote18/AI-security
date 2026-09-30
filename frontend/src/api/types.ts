// Mirrors backend/app/schemas/*.py. Kept hand-written rather than generated (openapi-typescript
// is a Should-tier addition per the project plan) so the frontend has no build-time dependency
// on a running backend.

export type RiskLevel = 'low' | 'medium' | 'high'
export type Classification = 'likely_legitimate' | 'suspicious' | 'likely_phishing'
export type AnalysisStatus = 'pending' | 'running' | 'completed' | 'failed'
export type AnalysisMode = 'standard' | 'deep'

export interface FeatureContributionOut {
  feature: string
  shap_value: number
}

export interface MlAnalysisOut {
  model_name: string
  probability: number
  threshold: number
  label: 0 | 1
  top_contributions: FeatureContributionOut[]
  latency_ms: number
}

export interface IndicatorOut {
  code: string
  severity: 'info' | 'low' | 'medium' | 'high'
  title: string
  description: string
  mitre_technique: string | null
}

export interface DnsRecordOut {
  record_type: string
  values: string[]
  error: string | null
}

export interface DomainInfoOut {
  registered_domain: string
  dns_records: DnsRecordOut[]
  dns_resolved: boolean
  registrar: string | null
  domain_created_at: string | null
  domain_age_days: number | null
  rdap_found: boolean
  degraded: boolean
}

export interface ThreatIntelOut {
  provider: string
  status: 'listed' | 'not_listed' | 'unavailable'
  threat_type: string | null
  tags: string[]
  reference_url: string | null
  error: string | null
}

export interface AnalysisStepOut {
  step: string
  status: string
  ms: number | null
  error: string | null
}

export interface AnalysisOut {
  id: string
  url: string
  status: AnalysisStatus
  mode: AnalysisMode
  steps: AnalysisStepOut[]
  risk_score: number | null
  risk_level: RiskLevel | null
  classification: Classification | null
  degraded: boolean
  error: string | null
  ml_analysis: MlAnalysisOut | null
  indicators: IndicatorOut[]
  domain_info: DomainInfoOut | null
  threat_intelligence: ThreatIntelOut[]
  created_at: string
  completed_at: string | null
}

export interface AnalysisSummaryOut {
  id: string
  url: string
  status: AnalysisStatus
  risk_score: number | null
  risk_level: RiskLevel | null
  classification: Classification | null
  created_at: string
}

export interface IndicatorExplanationOut {
  indicator_code: string
  explanation: string
  source_numbers: number[]
}

export interface SourceOut {
  chunk_id: string
  doc_id: string | null
  title: string | null
  source_name: string | null
  source_url: string | null
  topic: string | null
  score: number
}

export interface SecurityReportOut {
  id: string
  analysis_id: string
  status: 'completed' | 'failed'
  provider: string
  model_name: string
  prompt_version: string
  summary: string | null
  indicator_explanations: IndicatorExplanationOut[]
  recommendations: string[]
  sources: SourceOut[]
  error: string | null
  latency_ms: number
  created_at: string
}

export interface FeedbackOut {
  id: string
  analysis_id: string
  verdict: 'agree' | 'disagree'
  comment: string | null
}

export interface UserOut {
  id: string
  email: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in_minutes: number
}

export interface ApiErrorBody {
  detail?: string | { msg: string }[]
  title?: string
}
