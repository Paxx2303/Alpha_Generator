export type NotificationKind = 'success' | 'warning' | 'error'

export interface NotificationItem {
  kind: NotificationKind
  title: string
  body: string
}

export interface HistogramBucket {
  bucket: string
  count: number
}

export interface ActivityItem {
  timestamp: string
  icon: string
  message: string
}

export interface OverviewSummary {
  simulated: number
  passing: number
  submitted: number
  errors: number
  average_sharpe: number
  best_sharpe: number
}

export interface PipelineStage {
  status: string
  detail: string
}

export interface PipelineProgress {
  run_number: number
  done: number
  total: number
  stages: Record<string, PipelineStage>
}

export interface PipelineRun {
  run_id: string
  workflow_type: string
  strategy_type: string
  target_count: number
  submit_enabled: boolean
  dry_run: boolean
  status: string
  current_stage: string
  started_at: string
  finished_at?: string | null
  summary?: Record<string, unknown>
  tags?: Record<string, unknown>
}

export interface PipelineEvent {
  id: number
  run_id: string
  stage: string
  level: string
  event_type: string
  message: string
  alpha_expression?: string | null
  alpha_run_id?: number | null
  payload?: Record<string, unknown>
  created_at: string
}

export interface AlphaRow {
  id: number
  expression: string
  theme: string
  source: string
  generation_source?: string
  origin_agent?: string | null
  strategy_type: string
  status: string
  sharpe: number
  fitness: number
  annual_returns?: number
  turnover: number
  drawdown: number
  self_correlation: number
  pre_sim_confidence?: number | null
  post_sim_confidence?: number | null
  pre_sim_verdict?: string | null
  post_sim_verdict?: string | null
  pre_backtest_score?: number | null
  pre_backtest_passed?: boolean | null
  pre_backtest_metrics?: Record<string, number>
  simulation_failed?: boolean
  failure_note?: string | null
  needs_review?: boolean
  gate_failure_reason?: string | null
  submitted_at?: string | null
  created_at: string
}

export interface FailurePatternItem {
  reason: string
  label: string
  count: number
  fields: string[]
  sources: Array<{ source: string; count: number }>
  avg_sharpe: number
  examples: string[]
}

export interface FailurePatternResponse {
  items: FailurePatternItem[]
  total_fail_events: number
  recent_failed_alphas: number
}

export interface TheoryUsageItem {
  theory_id: string
  title: string
  domain: string
  generated: number
  passing: number
  submitted: number
  pass_rate: number
  avg_sharpe: number
}

export interface TheoryUsageResponse {
  items: TheoryUsageItem[]
  top: TheoryUsageItem[]
  summary: {
    tracked_theories: number
    used_theories: number
    unused_theories: number
  }
}

export interface TheoryEntry {
  id: string
  domain: string
  title: string
  sector_tags: string[]
  core_principle: string
  alpha_implication: string[]
  example_expression: string
  agent_reasoning: string[]
  source: string
  status?: string
  version?: number
  created_by?: string | null
  updated_at?: string
}

export interface ResearchArtifact {
  id: number
  run_id: string
  kind: string
  title: string
  query_text?: string | null
  content: string
  source_path?: string | null
  related_alpha_expression?: string | null
  score?: number | null
  created_at: string
}

export interface ExplanationDetail {
  theme: string
  hypothesis: string
  prompt_context: string
  expected_metrics: Record<string, unknown>
  risks: string[]
  theory_ids: string[]
  research_refs: string[]
  agent_reviews: Array<Record<string, unknown>>
  stage_notes: Record<string, unknown>
}

export interface AlphaAnalysis {
  creation_reason: string
  evidence_basis: string[]
  theory_basis: string[]
  implementation_logic: string[]
  confidence_notes: string[]
}

export interface AlphaDetailResponse {
  alpha: AlphaRow & Record<string, unknown>
  features: {
    fields: string[]
    operators: string[]
    theme: string
    hypothesis: string
  }
  field_info: Array<Record<string, string>>
  operator_info: Array<Record<string, string>>
  explanation: ExplanationDetail
  analysis: AlphaAnalysis
  matched_theories: TheoryEntry[]
  checks: Array<Record<string, unknown>>
  research: ResearchArtifact[]
  related_documents: Array<{ path: string; score: number; excerpt: string }>
}

export interface OverviewResponse {
  summary: OverviewSummary
  latest_run?: PipelineRun | null
  progress: PipelineProgress
  workflow_detail?: {
    current_task?: {
      timestamp: string
      stage: string
      status: string
      label: string
      detail: string
      alpha_expression?: string | null
    } | null
    current_alpha?: string | null
    simulation_queue: {
      active?: {
        ticket?: string | null
        expression?: string | null
        waiting_seconds?: number | null
      } | null
      waiting: Array<{
        ticket: string
        expression: string
        queued_at: number
      }>
      count: number
    }
    task_timeline: Array<{
      timestamp: string
      stage: string
      status: string
      label: string
      detail: string
      alpha_expression?: string | null
    }>
    research_basis: Array<{
      title: string
      kind: string
      query_text: string
      created_at: string
    }>
    theory_basis: Array<{
      title: string
      reason: string
      count: number
      source: string
    }>
  }
  feed: ActivityItem[]
  histogram: HistogramBucket[]
  alerts: NotificationItem[]
  best_alpha: AlphaRow[]
  latest_report?: Record<string, unknown> | null
}

export interface SettingsResponse {
  credentials: {
    worldquant_username: string
    worldquant_password_masked: string
    openrouter_api_key_masked: string
  }
  pipeline: {
    alphas_per_run: number
    region: string
    universe: string
    neutralization: string
    auto_submit: boolean
    sim_throttle: number
    max_daily_submissions: number
  }
  ai: {
    self_critique_rounds: number
    enable_research: boolean
    custom_research_prompt: string
  }
}

export interface SettingsTestResponse {
  status: string
  provider: string
  message: string
}

export interface OptionsResponse {
  strategy_options: string[]
  universe_options: string[]
  neutralization_options: string[]
  theory_domains: string[]
  theory_sectors: string[]
}
