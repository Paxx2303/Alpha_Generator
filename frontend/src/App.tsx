import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import {
  Link,
  NavLink,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
} from 'react-router-dom'

import { api } from './api'
import type {
  ActivityItem,
  AlphaDetailResponse,
  AlphaRow,
  FailurePatternResponse,
  OptionsResponse,
  OverviewResponse,
  PipelineEvent,
  PipelineRun,
  SettingsResponse,
  TheoryEntry,
  TheoryUsageResponse,
} from './types'

type LoadState<T> = {
  data: T | null
  loading: boolean
  error: string
}

type StudioCandidate = {
  expression: string
  source: string
  valid: boolean
  errors: string[]
}

type StudioChatMessage = {
  id: string
  role: 'user' | 'agent' | 'system'
  agent: string
  content: string
  createdAt: string
}

type PendingRun = {
  requestedAt: string
  status: 'launching' | 'waiting'
  stdoutLog?: string
  stderrLog?: string
}

const navItems = [
  { to: '/', label: 'Dashboard', icon: 'ti ti-layout-dashboard' },
  { to: '/alphas', label: 'Alphas', icon: 'ti ti-table' },
  { to: '/simulating', label: 'Simulating Now', icon: 'ti ti-cpu' },
  { to: '/theories', label: 'Theory Explorer', icon: 'ti ti-brain' },
  { to: '/skills', label: 'Agent Skills', icon: 'ti ti-award' },
  { to: '/studio', label: 'Agent Studio', icon: 'ti ti-messages' },
  { to: '/research', label: 'Research', icon: 'ti ti-search' },
  { to: '/logs', label: 'Logs', icon: 'ti ti-terminal' },
  { to: '/system-analysis', label: 'Gap Analysis', icon: 'ti ti-chart-bar' },
  { to: '/settings', label: 'Settings', icon: 'ti ti-settings' },
]

type AnalysisSignal = {
  label: string
  value: string
  detail: string
  tone: 'success' | 'warning' | 'danger' | 'neutral'
}

type AnalysisGap = {
  title: string
  summary: string
  impact: string
  route?: string
  routeLabel?: string
}

type BenchmarkRow = {
  label: string
  reference: string
  current: string
  status: 'complete' | 'partial' | 'missing' | 'bonus'
  note: string
}

type BenchmarkBlock = {
  title: string
  tag: string
  summary: string
  rows: BenchmarkRow[]
}

type ActionStep = {
  title: string
  priority: string
  summary: string
  route?: string
  routeLabel?: string
}

type WorkflowStepStatus = 'done' | 'active' | 'idle' | 'blocked'

type WorkflowStep = {
  label: string
  detail: string
  status: WorkflowStepStatus
}

const systemSignals: AnalysisSignal[] = [
  { label: 'Generation breadth', value: 'Strong', detail: 'Templates, LLM flow, reviews, and simulation are wired.', tone: 'success' },
  { label: 'Operator visibility', value: 'Thin', detail: 'Polling and file-based memory still hide why a run went well or badly.', tone: 'warning' },
  { label: 'Self-reflection', value: 'Missing', detail: 'No confidence, origin, or failure-pattern loop for agents yet.', tone: 'danger' },
  { label: 'Explainability', value: 'Improving', detail: 'Alpha-level analysis exists now, but run-level experimentation is still shallow.', tone: 'neutral' },
]

const uiGaps: AnalysisGap[] = [
  {
    title: 'Real-time feedback is still delayed',
    summary: 'Dashboard and Logs update on polling, so long pipeline runs feel out of sync with what is actually happening.',
    impact: 'Operators cannot trust the current stage at a glance, and Studio chat feels stalled without streaming.',
    route: '/logs',
    routeLabel: 'Open Logs',
  },
  {
    title: 'Alpha detail is fragile around missing explanation state',
    summary: 'If explanation persistence lags, the detail experience becomes brittle instead of guiding the user.',
    impact: 'This slows review exactly when the user wants to inspect a fresh alpha.',
    route: '/alphas',
    routeLabel: 'Open Alphas',
  },
  {
    title: 'Studio memory is local-first and easy to lose',
    summary: 'Chatspace lives in localStorage and candidate-pool management still lacks stronger guardrails.',
    impact: 'Human-in-the-loop exploration works, but session continuity is not dependable enough for heavier use.',
    route: '/studio',
    routeLabel: 'Open Studio',
  },
]

const backendGaps: AnalysisGap[] = [
  {
    title: 'No origin tracking per alpha candidate',
    summary: 'The system does not yet persist whether an expression came from DeerFlow, template logic, or a genetic branch.',
    impact: 'We cannot compare source quality or learn which generator family is actually outperforming.',
  },
  {
    title: 'No agent confidence loop',
    summary: 'Pre-simulation judgment is stored as text, but not as a comparable confidence score.',
    impact: 'Agents cannot be calibrated against reality, so reflection stays narrative instead of measurable.',
  },
  {
    title: 'Lessons learned are not query-first',
    summary: 'Recovery notes exist, but they are not exposed as structured retrieval for the next generation batch.',
    impact: 'The system keeps remembering, but it cannot ask itself targeted questions before trying again.',
  },
]

const benchmarkBlocks: BenchmarkBlock[] = [
  {
    title: 'Alpha-GPT (ACL 2025)',
    tag: 'Human-AI Interactive',
    summary: 'Alpha-GPT tracks quality across refinement loops. Alpha Generator has the research substrate, but not the loop metrics yet.',
    rows: [
      { label: 'Hierarchical RAG', reference: 'Present', current: 'Knowledge base RAG', status: 'partial', note: 'The retrieval foundation exists, but not as a layered reasoning trace.' },
      { label: 'Thought decomposition', reference: 'Present', current: 'Explanation layer', status: 'complete', note: 'Alpha-level reasoning is exposed in the monitor.' },
      { label: 'Alpha IC tracking', reference: 'Present', current: 'Missing', status: 'missing', note: 'Simulation results are not tracked as quality trajectory across refinement rounds.' },
      { label: '10-round search enhancement', reference: 'Present', current: 'Missing', status: 'missing', note: 'There is no automatic multi-round search loop with measurable uplift.' },
      { label: 'Seed-to-enhanced delta', reference: 'Present', current: 'Missing', status: 'missing', note: 'We cannot tell which refinement step actually improved the candidate most.' },
    ],
  },
  {
    title: 'Chain-of-Alpha (2025)',
    tag: 'Dual-chain architecture',
    summary: 'The current system has a strong generation chain, but the optimization chain still depends on people nudging it forward.',
    rows: [
      { label: 'Factor generation chain', reference: 'Present', current: 'Generation pipeline', status: 'complete', note: 'Candidate creation and simulation already form a clear chain.' },
      { label: 'Factor optimization chain', reference: 'Present', current: 'Missing', status: 'missing', note: 'There is no automatic refinement path that consumes backtest feedback and edits the expression.' },
      { label: 'Backtest feedback loop', reference: 'Automatic', current: 'Manual', status: 'missing', note: 'Reviewing failures still requires operator attention instead of closed-loop optimization.' },
      { label: 'Prior knowledge memory', reference: 'Present', current: 'Lessons learned memory', status: 'partial', note: 'Memory exists, but remains file-based rather than queryable at run time.' },
      { label: 'Human intervention', reference: 'None required', current: 'Studio available', status: 'bonus', note: 'Human-in-the-loop Studio is useful, but it does not replace the missing optimization chain.' },
    ],
  },
  {
    title: 'W&B / MLflow',
    tag: 'Experiment tracking',
    summary: 'This is the clearest operational gap. The pipeline runs, but it cannot yet explain itself the way a strong experiment system should.',
    rows: [
      { label: 'Per-step latency and cost', reference: 'Tracked', current: 'Missing', status: 'missing', note: 'We do not know how long DeerFlow spends, or which stage is most expensive.' },
      { label: 'Sweep comparison', reference: 'Tracked', current: 'Ad hoc', status: 'partial', note: 'Brute-force exploration exists, but not as a visual experiment matrix.' },
      { label: 'Run tagging', reference: 'Versioned', current: 'Missing', status: 'missing', note: 'Runs are not tied to research artifact version, git state, or seed lineage.' },
    ],
  },
  {
    title: 'WorldQuant scoring formula',
    tag: 'Domain',
    summary: 'The quality gate is better than before, but still too narrow compared with how WorldQuant style ranking should be judged.',
    rows: [
      { label: 'Fitness score in gate', reference: 'Core metric', current: 'Partial', status: 'partial', note: 'Sharpe and turnover are surfaced, but the gate still needs a first-class fitness view.' },
      { label: 'Portfolio-level correlation', reference: 'Tracked', current: 'Proxy only', status: 'missing', note: 'Token overlap is not enough to know whether an alpha truly adds novel portfolio value.' },
    ],
  },
]

const actionSteps: ActionStep[] = [
  {
    title: 'Add real-time event streaming',
    priority: 'Priority 1',
    summary: 'Ship SSE for pipeline events so Dashboard, Logs, and Studio stop feeling one step behind the run.',
    route: '/logs',
    routeLabel: 'Inspect Logs',
  },
  {
    title: 'Track agent provenance and confidence',
    priority: 'Priority 2',
    summary: 'Persist generation source, confidence, and verdict fields so the system can compare what agents predicted versus what simulation proved.',
  },
  {
    title: 'Build experiment tracking for runs',
    priority: 'Priority 3',
    summary: 'Tag runs by data version, research artifact, latency, and cost to make improvements explainable instead of anecdotal.',
    route: '/research',
    routeLabel: 'Open Research',
  },
  {
    title: 'Turn Theory Explorer into a feedback surface',
    priority: 'Priority 4',
    summary: 'Add theory usage analytics, pass-rate heat, and paper-to-alpha traceability so research can be steered instead of only read.',
    route: '/theories',
    routeLabel: 'Open Theory Explorer',
  },
]

const operatorQuestions = [
  'Which generator family produces the highest pass rate for momentum versus mean-reversion?',
  'Which failure mode is repeating most often across the last 20 rejected alphas?',
  'Did the latest run improve because of research quality, prompt quality, or simulation filters?',
  'Which theory entries are generating candidates but never producing a passable alpha?',
]

function usePolling<T>(loader: () => Promise<T>, deps: unknown[], intervalMs = 0): LoadState<T> & { refetch: () => Promise<void> } {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const run = async () => {
    setLoading((current) => (data === null ? true : current))
    try {
      const next = await loader()
      setData(next)
      setError('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const kickoff = window.setTimeout(() => {
      void run()
    }, 0)
    if (!intervalMs) return
    const timer = window.setInterval(() => {
      void run()
    }, intervalMs)
    return () => {
      window.clearTimeout(kickoff)
      window.clearInterval(timer)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading, error, refetch: run }
}

function Panel(props: { title: string; subtitle?: string; actions?: ReactNode; children: ReactNode }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <div>
          <p className="eyebrow">{props.title}</p>
          {props.subtitle ? <h2>{props.subtitle}</h2> : null}
        </div>
        {props.actions ? <div className="panel-actions">{props.actions}</div> : null}
      </div>
      {props.children}
    </section>
  )
}

function StatusPill({ value }: { value: string }) {
  return <span className={`status-pill status-${value.toLowerCase()}`}>{value.replace(/_/g, ' ')}</span>
}

function EmptyState({ message }: { message: string }) {
  return <div className="empty-state">{message}</div>
}

function LoadingState({ message = 'Loading…' }: { message?: string }) {
  return <div className="empty-state loading">{message}</div>
}

function ErrorState({ message }: { message: string }) {
  return <div className="empty-state error">{message}</div>
}

function formatNumber(value: unknown, digits = 2) {
  const num = Number(value ?? 0)
  if (!Number.isFinite(num)) return '0'
  return num.toFixed(digits)
}

function formatPercent(value: unknown, digits = 2) {
  const num = Number(value ?? 0)
  if (!Number.isFinite(num)) return '0%'
  return `${(num * 100).toFixed(digits)}%`
}

function formatDateTime(value: unknown) {
  const text = String(value ?? '')
  if (!text) return 'n/a'
  const stamp = new Date(text)
  if (Number.isNaN(stamp.getTime())) return text
  return stamp.toLocaleString()
}

function formatDurationSeconds(value: unknown) {
  const total = Number(value ?? 0)
  if (!Number.isFinite(total) || total <= 0) return 'just now'
  if (total < 60) return `${Math.round(total)}s`
  const minutes = Math.floor(total / 60)
  const seconds = Math.round(total % 60)
  if (minutes < 60) return `${minutes}m ${seconds}s`
  const hours = Math.floor(minutes / 60)
  return `${hours}h ${minutes % 60}m`
}

function formatLabel(value: string) {
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function ExpressionCode({ expression }: { expression: string }) {
  const parts = expression.split(/([A-Za-z_][A-Za-z0-9_]*|\d+(?:\.\d+)?)/g).filter(Boolean)
  return (
    <code className="expression-code">
      {parts.map((part, index) => {
        let className = 'token-punctuation'
        if (['rank', 'ts_mean', 'ts_delta', 'ts_std_dev', 'ts_corr', 'zscore'].includes(part)) className = 'token-operator'
        else if (['returns', 'close', 'volume', 'vwap'].includes(part)) className = 'token-field'
        else if (!Number.isNaN(Number(part))) className = 'token-number'
        return (
          <span key={`${part}-${index}`} className={className}>
            {part}
          </span>
        )
      })}
    </code>
  )
}

function MetricCard({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="metric-card">
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{detail}</span>
    </div>
  )
}

function WorkflowStepRail({ steps }: { steps: WorkflowStep[] }) {
  return (
    <div className="workflow-step-rail" aria-label="Workflow steps">
      {steps.map((step, index) => (
        <article key={step.label} className={`workflow-step-card step-${step.status}`}>
          <span className="workflow-step-index">{index + 1}</span>
          <div>
            <strong>{step.label}</strong>
            <p>{step.detail}</p>
          </div>
        </article>
      ))}
    </div>
  )
}

function CommandCard(props: {
  title: string
  detail: string
  actionLabel: string
  disabled?: boolean
  tone?: 'primary' | 'neutral'
  onAction: () => void
}) {
  return (
    <article className={`command-card tone-${props.tone ?? 'neutral'}`}>
      <div>
        <p className="eyebrow">{props.title}</p>
        <strong>{props.detail}</strong>
      </div>
      <button className="ghost-button" onClick={props.onAction} disabled={props.disabled}>
        {props.actionLabel}
      </button>
    </article>
  )
}

function AnalysisSignalCard({ signal }: { signal: AnalysisSignal }) {
  return (
    <article className={`analysis-signal-card tone-${signal.tone}`}>
      <p className="eyebrow">{signal.label}</p>
      <strong>{signal.value}</strong>
      <span>{signal.detail}</span>
    </article>
  )
}

function BenchmarkBadge({ status }: { status: BenchmarkRow['status'] }) {
  const labelMap: Record<BenchmarkRow['status'], string> = {
    complete: 'OK',
    partial: 'Partial',
    missing: 'Missing',
    bonus: 'Bonus',
  }
  return <span className={`benchmark-badge is-${status}`}>{labelMap[status]}</span>
}

function renderInline(text: string): React.ReactNode {
  if (!text) return '';
  const parts: React.ReactNode[] = [];
  let remaining = text;
  while (remaining) {
    const codeIndex = remaining.indexOf('`');
    const boldIndex = remaining.indexOf('**');
    const linkMatch = remaining.match(/\[([^\]]+)\]\(([^)]+)\)/);
    
    let minIndex = Infinity;
    let type: 'code' | 'bold' | 'link' | 'none' = 'none';
    let matchLength = 0;
    let content = '';
    let linkUrl = '';
    
    if (codeIndex !== -1 && codeIndex < minIndex) {
      const closingIndex = remaining.indexOf('`', codeIndex + 1);
      if (closingIndex !== -1) {
        minIndex = codeIndex;
        type = 'code';
        matchLength = closingIndex - codeIndex + 1;
        content = remaining.substring(codeIndex + 1, closingIndex);
      }
    }
    
    if (boldIndex !== -1 && boldIndex < minIndex) {
      const closingIndex = remaining.indexOf('**', boldIndex + 2);
      if (closingIndex !== -1) {
        minIndex = boldIndex;
        type = 'bold';
        matchLength = closingIndex - boldIndex + 2;
        content = remaining.substring(boldIndex + 2, closingIndex);
      }
    }
    
    if (linkMatch && linkMatch.index !== undefined && linkMatch.index < minIndex) {
      minIndex = linkMatch.index;
      type = 'link';
      matchLength = linkMatch[0].length;
      content = linkMatch[1];
      linkUrl = linkMatch[2];
    }
    
    if (type === 'none' || minIndex === Infinity) {
      parts.push(remaining);
      break;
    }
    
    if (minIndex > 0) {
      parts.push(remaining.substring(0, minIndex));
    }
    
    if (type === 'code') {
      parts.push(<code key={remaining.length + minIndex} className="md-inline-code">{content}</code>);
    } else if (type === 'bold') {
      parts.push(<strong key={remaining.length + minIndex}>{content}</strong>);
    } else if (type === 'link') {
      parts.push(
        <a key={remaining.length + minIndex} href={linkUrl} target="_blank" rel="noopener noreferrer" className="md-link">
          {content}
        </a>
      );
    }
    
    remaining = remaining.substring(minIndex + matchLength);
  }
  return parts;
}

function MarkdownRenderer({ text }: { text: string }): React.ReactNode {
  if (!text) return null;
  const lines = text.split('\n');
  const elements: React.ReactNode[] = [];
  
  let inCode = false;
  let codeLines: string[] = [];
  let codeLang = '';
  
  let inTable = false;
  let tableRows: string[][] = [];
  
  let inList = false;
  let listItems: { text: string; type: 'ul' | 'ol' }[] = [];
  
  let inBlockquote = false;
  let quoteLines: string[] = [];

  const flush = () => {
    if (inCode) {
      elements.push(
        <pre key={elements.length} className="md-code-block">
          {codeLang ? <div className="code-lang">{codeLang}</div> : null}
          <code>{codeLines.join('\n')}</code>
        </pre>
      );
      inCode = false;
      codeLines = [];
      codeLang = '';
    }
    if (inTable) {
      if (tableRows.length > 0) {
        const filteredRows = tableRows.filter(row => !row.every(cell => cell.trim().match(/^-+$/)));
        if (filteredRows.length > 0) {
          const headers = filteredRows[0];
          const dataRows = filteredRows.slice(1);
          elements.push(
            <div key={elements.length} className="md-table-wrapper">
              <table className="md-table">
                <thead>
                  <tr>
                    {headers.map((h, i) => <th key={i}>{renderInline(h)}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {dataRows.map((row, ri) => (
                    <tr key={ri}>
                      {row.map((cell, ci) => <td key={ci}>{renderInline(cell)}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          );
        }
      }
      inTable = false;
      tableRows = [];
    }
    if (inList) {
      if (listItems.length > 0) {
        const type = listItems[0].type;
        const Tag = type === 'ol' ? 'ol' : 'ul';
        elements.push(
          <Tag key={elements.length} className={`md-list md-${type}`}>
            {listItems.map((item, i) => <li key={i}>{renderInline(item.text)}</li>)}
          </Tag>
        );
      }
      inList = false;
      listItems = [];
    }
    if (inBlockquote) {
      if (quoteLines.length > 0) {
        const fullQuote = quoteLines.join('\n');
        let alertType: 'note' | 'tip' | 'important' | 'warning' | 'caution' | 'default' = 'default';
        let cleanText = fullQuote;
        const alertMatch = fullQuote.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*(.*)$/is);
        if (alertMatch) {
          alertType = alertMatch[1].toLowerCase() as any;
          cleanText = alertMatch[2];
        }
        elements.push(
          <blockquote key={elements.length} className={`md-blockquote md-alert-${alertType}`}>
            {alertType !== 'default' ? <strong className="alert-badge">{alertType.toUpperCase()}</strong> : null}
            <div>{MarkdownRenderer({ text: cleanText })}</div>
          </blockquote>
        );
      }
      inBlockquote = false;
      quoteLines = [];
    }
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed.startsWith('```')) {
      if (inCode) {
        flush();
      } else {
        flush();
        inCode = true;
        codeLang = trimmed.slice(3).trim();
      }
      continue;
    }

    if (inCode) {
      codeLines.push(line);
      continue;
    }

    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      flush();
      inTable = true;
      const cells = line.split('|').slice(1, -1).map(c => c.trim());
      tableRows.push(cells);
      continue;
    } else if (inTable) {
      flush();
    }

    if (trimmed.startsWith('>')) {
      if (!inBlockquote) {
        flush();
        inBlockquote = true;
      }
      const quoteText = line.replace(/^\s*>\s?/, '');
      quoteLines.push(quoteText);
      continue;
    } else if (inBlockquote) {
      if (trimmed !== '') {
        flush();
      }
    }

    if (trimmed === '---' || trimmed === '***' || trimmed === '___') {
      flush();
      elements.push(<hr key={elements.length} className="md-hr" />);
      continue;
    }

    const headerMatch = line.match(/^(#{1,6})\s+(.*)$/);
    if (headerMatch) {
      flush();
      const level = headerMatch[1].length;
      const title = headerMatch[2];
      const Tag = `h${level}` as 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
      elements.push(<Tag key={elements.length} className={`md-h md-${Tag}`}>{renderInline(title)}</Tag>);
      continue;
    }

    const ulMatch = line.match(/^(\s*)[-*+]\s+(.*)$/);
    const olMatch = line.match(/^(\s*)\d+\.\s+(.*)$/);
    if (ulMatch) {
      if (!inList) {
        flush();
        inList = true;
      }
      listItems.push({ text: ulMatch[2], type: 'ul' });
      continue;
    } else if (olMatch) {
      if (!inList) {
        flush();
        inList = true;
      }
      listItems.push({ text: olMatch[2], type: 'ol' });
      continue;
    } else if (inList && trimmed === '') {
      flush();
      continue;
    }

    if (trimmed === '') {
      flush();
      continue;
    }

    flush();
    elements.push(<p key={elements.length} className="md-p">{renderInline(line)}</p>);
  }

  flush();
  return <div className="md-preview">{elements}</div>;
}

function DualAgentChatspace({ strategyType = 'momentum' }: { strategyType?: string }) {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<StudioChatMessage[]>([])
  const [busy, setBusy] = useState(false)
  const feedRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    void api.getChatMessages('dashboard', 40).then((res) => {
      const items = (res.items ?? []).map((m: Record<string, unknown>) => ({
        id: String(m.id ?? ''),
        role: String(m.role ?? 'user') as 'user' | 'agent' | 'system',
        agent: String(m.agent ?? ''),
        content: String(m.content ?? ''),
        createdAt: String(m.created_at ?? ''),
      }))
      setMessages(items)
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight
  }, [messages])

  const send = async () => {
    const prompt = input.trim()
    if (!prompt) return
    setBusy(true)
    const stamp = new Date().toISOString()
    const userMsg: StudioChatMessage = { id: `${stamp}-user`, role: 'user', agent: 'User', content: prompt, createdAt: stamp }
    setMessages((c) => [...c, userMsg])
    setInput('')
    void api.postChatMessage({ session: 'dashboard', role: 'user', agent: 'User', content: prompt }).catch(() => {})
    try {
      const result = await api.studioQuery({ target: 'Both', prompt: `[strategy=${strategyType}] ${prompt}` })
      const replies = (result.responses ?? {}) as Record<string, string>
      const agentMsgs: StudioChatMessage[] = Object.entries(replies).map(([agent, content], i) => ({
        id: `${stamp}-${agent}-${i}`, role: 'agent', agent, content, createdAt: stamp,
      }))
      setMessages((c) => [...c, ...agentMsgs])
      for (const msg of agentMsgs) {
        void api.postChatMessage({ session: 'dashboard', role: 'agent', agent: msg.agent, content: msg.content }).catch(() => {})
      }
    } catch (err) {
      const errMsg: StudioChatMessage = { id: `${stamp}-err`, role: 'system', agent: 'System', content: err instanceof Error ? err.message : 'Request failed', createdAt: stamp }
      setMessages((c) => [...c, errMsg])
    } finally {
      setBusy(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send() }
  }

  return (
    <div className="gemini-chatspace">
      <div className="gemini-feed" ref={(el) => { feedRef.current = el }}>
        {messages.length ? (
          messages.map((msg) => (
            <article key={msg.id} className={`gemini-bubble gemini-${msg.role}`}>
              <div className="gemini-avatar">{msg.role === 'user' ? 'U' : msg.agent.charAt(0)}</div>
              <div className="gemini-bubble-body">
                <div className="gemini-bubble-head">
                  <strong>{msg.role === 'user' ? 'You' : msg.agent}</strong>
                  <span>{msg.createdAt.slice(11, 19)}</span>
                </div>
                <MarkdownRenderer text={msg.content} />
              </div>
            </article>
          ))
        ) : (
          <div className="gemini-empty">
            <strong>DeerFlow Chatspace</strong>
            <p>Ask DeerFlow anything about your alpha pipeline.</p>
          </div>
        )}
        {busy ? <div className="gemini-typing"><span /><span /><span /></div> : null}
      </div>
      <div className="gemini-compose">
        <textarea
          rows={1}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask both agents…"
        />
        <button className="gemini-send" onClick={() => void send()} disabled={busy} aria-label="Send">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 2L11 13" /><path d="M22 2L15 22L11 13L2 9L22 2Z" /></svg>
        </button>
      </div>
    </div>
  )
}

function CredentialInput(props: {
  label: string
  value: string
  placeholder?: string
  revealed: boolean
  onToggle: () => void
  onChange: (value: string) => void
  onTest?: () => Promise<void>
}) {
  const handleTest = props.onTest
  return (
    <label>
      {props.label}
      <div className="credential-row">
        <input
          type={props.revealed ? 'text' : 'password'}
          placeholder={props.placeholder}
          value={props.value}
          onChange={(event) => props.onChange(event.target.value)}
        />
        <button type="button" className="icon-button" aria-label={props.revealed ? 'eye-off' : 'eye'} onClick={props.onToggle}>
          {props.revealed ? 'eye-off' : 'eye'}
        </button>
        {handleTest ? (
          <button type="button" className="ghost-button" onClick={() => void handleTest()}>
            Test connection
          </button>
        ) : null}
      </div>
    </label>
  )
}

function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const overviewState = usePolling<OverviewResponse>(() => api.getOverview(), [location.pathname], 2000)
  const optionsState = usePolling<OptionsResponse>(() => api.getOptions(), [], 0)
  const [toast, setToast] = useState('')
  const [runBusy, setRunBusy] = useState(false)
  const [pendingRun, setPendingRun] = useState<PendingRun | null>(null)

  const triggerRun = async () => {
    try {
      setRunBusy(true)
      const requestedAt = new Date().toISOString()
      setPendingRun({ requestedAt, status: 'launching' })
      const result = await api.startRun({ strategy_type: 'momentum', submit_enabled: false, dry_run: false })
      setToast(`Pipeline started. PID ${String(result.pid ?? '')}`.trim())
      setPendingRun({
        requestedAt,
        status: 'waiting',
        stdoutLog: String(result.stdout_log ?? ''),
        stderrLog: String(result.stderr_log ?? ''),
      })
      void overviewState.refetch()
      void (async () => {
        for (let attempt = 0; attempt < 12; attempt += 1) {
          await new Promise((resolve) => window.setTimeout(resolve, 1000))
          await overviewState.refetch()
        }
      })()
    } catch (err) {
      setToast(err instanceof Error ? err.message : 'Failed to start pipeline')
      setPendingRun(null)
    } finally {
      setRunBusy(false)
    }
  }

  const triggerStop = async () => {
    try {
      const result = await api.stopRun()
      const pids = Array.isArray(result.pids) ? result.pids.join(', ') : ''
      setToast(pids ? `Stopped pipeline PID(s): ${pids}` : 'No active pipeline job found.')
      void overviewState.refetch()
    } catch (err) {
      setToast(err instanceof Error ? err.message : 'Failed to stop pipeline')
    }
  }

  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(() => setToast(''), 5000)
    return () => window.clearTimeout(timer)
  }, [toast])

  useEffect(() => {
    if (!pendingRun || !overviewState.data?.latest_run) return
    const latestStarted = String(overviewState.data.latest_run.started_at || '')
    if (!latestStarted) return
    if (new Date(latestStarted).getTime() >= new Date(pendingRun.requestedAt).getTime() - 1000) {
      setPendingRun(null)
    }
  }, [overviewState.data, pendingRun])

  return (
    <div className="app-layout">
      <aside className="app-sidebar">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) => `sicon ${isActive ? 'active' : ''}`}
            title={item.label}
          >
            <i className={item.icon}></i>
          </NavLink>
        ))}
      </aside>

      <div className="main-layout">
        <header className="topbar-layout">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--color-text-primary)' }}>WQ Brain Alpha Monitor</span>
            <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>/</span>
            <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              {navItems.find((item) => item.to === location.pathname || (item.to !== '/' && location.pathname.startsWith(item.to)))?.label ?? 'Monitor'}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className={`badge ${overviewState.error ? 'b-red' : 'b-green'}`}>
              {overviewState.error ? 'API Offline' : 'API Live'}
            </span>
            <button className="btn-layout btn-sm-layout" onClick={() => void triggerRun()} disabled={runBusy}>
              {runBusy ? 'Starting...' : 'Run Now'}
            </button>
            <button className="btn-layout btn-sm-layout" style={{ color: 'var(--color-text-danger)' }} onClick={() => void triggerStop()}>
              Stop
            </button>
          </div>
        </header>

        {toast ? <div className="toast" style={{ margin: '10px 14px 0 14px' }}>{toast}</div> : null}

        <main className="content-layout">
          <Routes>
            <Route path="/" element={<DashboardPage overviewState={overviewState} onRun={triggerRun} onStop={triggerStop} pendingRun={pendingRun} />} />
            <Route path="/alphas" element={<AlphasPage />} />
            <Route path="/alphas/:alphaId" element={<AlphaDetailPage />} />
            <Route path="/simulating" element={<SimulatingPage overviewState={overviewState} onStop={triggerStop} />} />
            <Route path="/skills" element={<AgentSkillsPage />} />
            <Route path="/research" element={<ResearchPage />} />
            <Route path="/logs" element={<LogsPage />} />
            <Route path="/system-analysis" element={<SystemAnalysisPage />} />
            <Route path="/settings" element={<SettingsPage options={optionsState.data} />} />
            <Route path="/theories" element={<TheoriesPage options={optionsState.data} />} />
            <Route
              path="/studio"
              element={<StudioPage options={optionsState.data} overview={overviewState.data} onInspectAlpha={(id) => navigate(`/alphas/${id}`)} />}
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

function DashboardPage(props: {
  overviewState: LoadState<OverviewResponse> & { refetch: () => Promise<void> }
  onRun: () => Promise<void>
  onStop: () => Promise<void>
  pendingRun?: PendingRun | null
}) {
  if (props.overviewState.loading && !props.overviewState.data) return <LoadingState message="Loading pipeline monitor…" />
  if (props.overviewState.error && !props.overviewState.data) return <ErrorState message={props.overviewState.error} />
  const data = props.overviewState.data
  if (!data) return <EmptyState message="No dashboard data available." />
  const workflowDetail = data.workflow_detail
  const currentTask = workflowDetail?.current_task
  const queue = workflowDetail?.simulation_queue
  const latestRun = data.latest_run
  const pendingRunIsAhead =
    !!props.pendingRun &&
    (!latestRun || new Date(String(latestRun.started_at || 0)).getTime() < new Date(props.pendingRun.requestedAt).getTime() - 1000)
  const visibleCurrentTask =
    (!pendingRunIsAhead ? currentTask : null) ??
    (props.pendingRun
      ? {
          label: 'Run launch requested',
          detail:
            props.pendingRun.status === 'launching'
              ? 'Sending run request to backend.'
              : 'Waiting for the pipeline process to register its first research task.',
        }
      : null)
  const completedStages = Object.values(data.progress.stages).filter((stage) => stage.status === 'done').length
  const totalStages = Math.max(Object.keys(data.progress.stages).length, 1)
  const progressRatio = data.progress.total
    ? Math.min(1, data.progress.done / Math.max(data.progress.total, 1))
    : completedStages / totalStages

  return (
    <div style={{ padding: '0 4px' }}>
      {/* Metrics Grid */}
      <div className="card" style={{ display: 'flex', gap: '12px', padding: '12px', marginBottom: '12px' }}>
        <div className="metric-widget" style={{ flex: 1 }}>
          <div className="metric-label">Alphas simulated</div>
          <div className="metric-val">{data.summary.simulated}</div>
          <div className="metric-sub">{data.summary.passing} passing</div>
        </div>
        <div className="metric-widget" style={{ flex: 1 }}>
          <div className="metric-label">Queue count</div>
          <div className="metric-val">{queue?.count ?? 0}</div>
          <div className="metric-sub">{queue?.active?.expression ? 'active: ' + queue.active.expression.substring(0, 15) + '...' : 'idle'}</div>
        </div>
        <div className="metric-widget" style={{ flex: 1 }}>
          <div className="metric-label">Gate pass rate</div>
          <div className="metric-val">
            {data.summary.simulated > 0 ? Math.round((data.summary.passing / data.summary.simulated) * 100) : 0}%
          </div>
          <div className="metric-sub">Structured quality gates</div>
        </div>
        <div className="metric-widget" style={{ flex: 1 }}>
          <div className="metric-label">Best Sharpe</div>
          <div className="metric-val">{formatNumber(data.summary.best_sharpe, 2)}</div>
          <div className="metric-sub">{formatNumber(data.summary.average_sharpe, 2)} avg Sharpe</div>
        </div>
      </div>

      {/* Active Run Card */}
      <div className="card" style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <div>
            <div style={{ fontSize: '11px', color: 'var(--color-text-tertiary)', textTransform: 'uppercase' }}>Active Run</div>
            <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--color-text-primary)' }}>
              {data.latest_run?.run_id ?? (props.pendingRun ? 'RUN_LAUNCHING' : 'NO_ACTIVE_RUN')}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <span className={`pulse-dot ${latestRun?.status === 'running' ? 'running' : latestRun?.status === 'error' ? 'warn' : ''}`}></span>
            <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              {props.pendingRun ? 'Launching stage' : latestRun ? `${formatLabel(latestRun.status)} — ${formatLabel(latestRun.current_stage)}` : 'Idle'}
            </span>
          </div>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--color-text-secondary)', marginBottom: '4px' }}>
          <span>Simulation progress</span>
          <span>{Math.round(progressRatio * 100)}% ({data.progress.total ? `${data.progress.done}/${data.progress.total} candidates` : `${completedStages}/${totalStages} stages`})</span>
        </div>
        <div style={{ height: '6px', background: 'var(--color-background-tertiary)', borderRadius: '3px', overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${Math.max(progressRatio * 100, 4)}%`, background: '#185FA5' }}></div>
        </div>
      </div>

      {/* Double Column Block */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
        {/* Left Column: Live Activity */}
        <div className="card" style={{ flex: 1 }}>
          <div className="sec">Live Activity</div>
          {data.feed.length ? (
            data.feed.slice(0, 6).map((item: ActivityItem, idx) => (
              <div key={`${item.timestamp}-${item.message}-${idx}`} className="insight-row-layout">
                <span className="insight-icon-layout">{item.icon}</span>
                <span style={{ color: 'var(--color-text-secondary)', fontSize: '12px' }}>{item.message}</span>
                <span style={{ marginLeft: 'auto', fontSize: '10px', color: 'var(--color-text-tertiary)' }}>{item.timestamp}</span>
              </div>
            ))
          ) : (
            <EmptyState message="No events yet." />
          )}
        </div>

        {/* Right Column: Best Passing Alphas */}
        <div className="card" style={{ flex: 1 }}>
          <div className="sec">Best Passing Alphas</div>
          {data.best_alpha.length ? (
            data.best_alpha.slice(0, 6).map((item) => (
              <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', padding: '6px 0', borderBottom: '0.5px solid var(--color-border-tertiary)' }}>
                <span style={{ color: 'var(--color-text-primary)', fontFamily: 'monospace' }} title={item.expression}>
                  <Link to={`/alphas/${item.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                    {item.expression.length > 35 ? item.expression.substring(0, 35) + '...' : item.expression}
                  </Link>
                </span>
                <span className={`badge ${item.sharpe >= 2 ? 'b-green' : 'b-amber'}`}>
                  Sharpe {formatNumber(item.sharpe, 2)}
                </span>
              </div>
            ))
          ) : (
            <EmptyState message="No passing alphas yet today." />
          )}
        </div>
      </div>

      {/* Alerts and Controls */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
        <Panel title="Mission Control" subtitle="Next best move for the current alpha workflow">
          <div style={{ padding: '8px 0' }}>
            <h4 style={{ fontSize: '13px', color: 'var(--color-text-primary)', marginBottom: '4px' }}>
              {visibleCurrentTask?.label ?? 'Ready for the next run'}
            </h4>
            <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
              {visibleCurrentTask?.detail ??
                (latestRun
                  ? `${formatLabel(latestRun.status)} at ${formatLabel(latestRun.current_stage)}.`
                  : 'Start a dry operational pass, inspect the first research basis, then move promising candidates into Studio.')}
            </p>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                className="btn-layout btn-sm-layout"
                style={{ background: 'var(--color-text-info)', color: '#000' }}
                disabled={!!props.pendingRun}
                onClick={() => void props.onRun()}
              >
                {props.pendingRun ? 'Launching...' : 'Run Now'}
              </button>
              <button
                className="btn-layout btn-sm-layout"
                disabled={latestRun?.status !== 'running' && !props.pendingRun}
                onClick={() => void props.onStop()}
              >
                Stop Run
              </button>
              <button
                className="btn-layout btn-sm-layout"
                style={{ background: 'transparent', border: '0.5px solid var(--color-border-secondary)' }}
                onClick={() => void props.overviewState.refetch()}
              >
                Refresh
              </button>
            </div>
          </div>
        </Panel>

        <Panel title="Alerts" subtitle="Submission and runtime signals">
          {data.alerts.length ? (
            <div style={{ maxHeight: '140px', overflowY: 'auto' }}>
              {data.alerts.map((alert, idx) => (
                <div key={`${alert.title}-${idx}`} style={{ padding: '6px 8px', borderRadius: '4px', background: alert.kind === 'error' ? '#FCEBEB' : alert.kind === 'warning' ? '#FAEEDA' : 'var(--color-background-primary)', color: alert.kind === 'error' ? '#A32D2D' : alert.kind === 'warning' ? '#854F0B' : 'var(--color-text-primary)', marginBottom: '4px', fontSize: '11px' }}>
                  <strong>{alert.title}</strong>: {alert.body}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState message="No alerts yet." />
          )}
        </Panel>
      </div>

      {/* DeerFlow Chatspace */}
      <Panel title="DeerFlow Chatspace" subtitle="Talk to DeerFlow without leaving the dashboard">
        <DualAgentChatspace strategyType={latestRun?.strategy_type ?? 'momentum'} />
      </Panel>
    </div>
  )
}

function SystemAnalysisPage() {
  const failureState = usePolling<FailurePatternResponse>(() => api.getFailurePatterns(240), [], 15000)
  const theoryUsageState = usePolling<TheoryUsageResponse>(() => api.getTheoryUsage(320), [], 15000)

  return (
    <div className="page-grid">
      <Panel title="System Audit" subtitle="Alpha Generator works, but still thinks in snapshots">
        <div className="analysis-hero">
          <div className="analysis-hero-copy">
            <p className="analysis-lead">
              The platform already covers multi-source generation, dual-agent review, structured quality gates, and alpha-level explainability.
              What it still lacks is operational memory: real-time visibility, experiment traceability, and measurable self-reflection.
            </p>
            <div className="tag-row">
              <span className="tag">Runs today: generation, simulation, explainability</span>
              <span className="tag">Missing next: streaming, provenance, loop metrics</span>
            </div>
          </div>
          <div className="analysis-scoreboard">
            {systemSignals.map((signal) => (
              <AnalysisSignalCard key={signal.label} signal={signal} />
            ))}
          </div>
        </div>
      </Panel>

      <Panel title="Where The Friction Is" subtitle="The most visible pain points for operators today">
        <div className="analysis-card-grid">
          {uiGaps.map((gap) => (
            <article key={gap.title} className="analysis-card">
              <p className="eyebrow">UI gap</p>
              <h3>{gap.title}</h3>
              <p>{gap.summary}</p>
              <strong>Why it matters</strong>
              <p>{gap.impact}</p>
              {gap.route && gap.routeLabel ? (
                <Link className="inline-link" to={gap.route}>
                  {gap.routeLabel}
                </Link>
              ) : null}
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Backend Reflection Gaps" subtitle="What prevents the agents from learning about their own quality">
        <div className="analysis-card-grid">
          {backendGaps.map((gap) => (
            <article key={gap.title} className="analysis-card analysis-card-danger">
              <p className="eyebrow">ML ops gap</p>
              <h3>{gap.title}</h3>
              <p>{gap.summary}</p>
              <strong>What this blocks</strong>
              <p>{gap.impact}</p>
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Benchmark Comparison" subtitle="How the system compares against stronger research and tracking patterns">
        <div className="benchmark-grid">
          {benchmarkBlocks.map((block) => (
            <article key={block.title} className="benchmark-card">
              <div className="benchmark-card-header">
                <div>
                  <h3>{block.title}</h3>
                  <span className="benchmark-tag">{block.tag}</span>
                </div>
                <p>{block.summary}</p>
              </div>
              <div className="benchmark-table">
                {block.rows.map((row) => (
                  <div key={row.label} className="benchmark-row">
                    <div className="benchmark-axis">
                      <strong>{row.label}</strong>
                      <span>Reference: {row.reference}</span>
                    </div>
                    <div className="benchmark-current">
                      <span>{row.current}</span>
                      <BenchmarkBadge status={row.status} />
                    </div>
                    <p>{row.note}</p>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Questions The System Still Cannot Answer" subtitle="These are the observability gaps behind the current friction">
        <div className="analysis-question-list">
          {operatorQuestions.map((question) => (
            <article key={question} className="analysis-question-card">
              <span className="analysis-question-mark">?</span>
              <p>{question}</p>
            </article>
          ))}
        </div>
      </Panel>

      <Panel title="Live Failure Patterns" subtitle="Structured gate and simulation failures from recent runs">
        {failureState.loading && !failureState.data ? <LoadingState message="Loading failure patterns..." /> : null}
        {failureState.error && !failureState.data ? <ErrorState message={failureState.error} /> : null}
        {failureState.data?.items?.length ? (
          <div className="analysis-card-grid">
            {failureState.data.items.slice(0, 6).map((item) => (
              <article key={item.reason} className="analysis-card">
                <p className="eyebrow">{item.count} recent hits</p>
                <h3>{item.label}</h3>
                <p>Average Sharpe at failure: {formatNumber(item.avg_sharpe)}</p>
                <p>{item.fields.length ? `Common fields: ${item.fields.join(', ')}` : 'No dominant metric field captured yet.'}</p>
                <p>{item.sources.length ? `Source mix: ${item.sources.map((source) => `${source.source} ${source.count}`).join(' · ')}` : 'No source breakdown yet.'}</p>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState message="No structured failure patterns recorded yet." />
        )}
      </Panel>

      <Panel title="Theory Usage Heat" subtitle="Which theories are actually producing alpha candidates and passes">
        {theoryUsageState.loading && !theoryUsageState.data ? <LoadingState message="Loading theory usage..." /> : null}
        {theoryUsageState.error && !theoryUsageState.data ? <ErrorState message={theoryUsageState.error} /> : null}
        {theoryUsageState.data ? (
          <>
            <div className="metrics-grid">
              <MetricCard
                label="Tracked theories"
                value={String(theoryUsageState.data.summary.tracked_theories)}
                detail={`${theoryUsageState.data.summary.used_theories} already used in alpha explanations`}
              />
              <MetricCard
                label="Unused theories"
                value={String(theoryUsageState.data.summary.unused_theories)}
                detail="Good targets for exploration or pruning"
              />
              <MetricCard
                label="Top linked theories"
                value={String(theoryUsageState.data.top.length)}
                detail="Theories with measurable generation activity"
              />
              <MetricCard
                label="Best explorer signal"
                value={theoryUsageState.data.top[0] ? `${Math.round(theoryUsageState.data.top[0].pass_rate * 100)}%` : '0%'}
                detail={theoryUsageState.data.top[0] ? theoryUsageState.data.top[0].title : 'Waiting for theory-linked runs'}
              />
            </div>
            <div className="analysis-card-grid">
              {theoryUsageState.data.top.slice(0, 6).map((item) => (
                <article key={item.theory_id} className="analysis-card">
                  <p className="eyebrow">{item.domain}</p>
                  <h3>{item.title}</h3>
                  <p>Generated {item.generated} alpha links, with {item.passing} passes and {item.submitted} submissions.</p>
                  <p>Pass rate {formatPercent(item.pass_rate)} · Avg Sharpe {formatNumber(item.avg_sharpe)}</p>
                  <Link className="inline-link" to={`/theories`}>
                    Open Theory Explorer
                  </Link>
                </article>
              ))}
            </div>
          </>
        ) : null}
      </Panel>

      <Panel title="Build Next" subtitle="A practical roadmap from usable to truly operable">
        <div className="roadmap-grid">
          {actionSteps.map((step) => (
            <article key={step.title} className="roadmap-card">
              <span className="roadmap-priority">{step.priority}</span>
              <h3>{step.title}</h3>
              <p>{step.summary}</p>
              {step.route && step.routeLabel ? (
                <Link className="inline-link" to={step.route}>
                  {step.routeLabel}
                </Link>
              ) : null}
            </article>
          ))}
        </div>
      </Panel>
    </div>
  )
}

function AlphasPage() {
  const [status, setStatus] = useState('')
  const [search, setSearch] = useState('')
  const [sharpeMin, setSharpeMin] = useState('0')
  const [theme, setTheme] = useState('')
  const state = usePolling(
    () => api.getAlphas({ status, search, sharpe_min: sharpeMin || undefined, theme }),
    [status, search, sharpeMin, theme],
    10000,
  )

  if (state.loading && !state.data) return <LoadingState message="Loading alpha pool…" />
  if (state.error && !state.data) return <ErrorState message={state.error} />
  const rows = (state.data?.items ?? []) as unknown as AlphaRow[]
  const themes = Array.from(new Set(rows.map((item) => item.theme))).sort()

  return (
    <div style={{ padding: '0 4px' }}>
      <Panel title="Alpha Pool" subtitle="Filter, compare, and inspect candidates">
        <div className="filter-grid" style={{ marginBottom: '14px' }}>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All status</option>
            <option value="approved">Pass</option>
            <option value="submitted">Submitted</option>
            <option value="tested">Fail</option>
            <option value="invalid">Invalid</option>
            <option value="screened_out">Screened out</option>
          </select>
          <select value={sharpeMin} onChange={(event) => setSharpeMin(event.target.value)}>
            <option value="0">Sharpe ≥ 0</option>
            <option value="0.5">Sharpe ≥ 0.5</option>
            <option value="1">Sharpe ≥ 1.0</option>
            <option value="1.5">Sharpe ≥ 1.5</option>
          </select>
          <select value={theme} onChange={(event) => setTheme(event.target.value)}>
            <option value="">All themes</option>
            {themes.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search expression" />
        </div>

        {rows.length ? (
          <div style={{ overflowX: 'auto' }}>
            <table className="tbl-layout">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Expression</th>
                  <th>Theme</th>
                  <th>Sharpe</th>
                  <th>Fitness</th>
                  <th>Turnover</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const statusStr = String(row.status || '');
                  const isPassing = statusStr === 'approved' || statusStr === 'submitted' || row.sharpe >= 2.0;
                  const isFailed = statusStr === 'tested' || row.simulation_failed || statusStr === 'invalid' || statusStr === 'screened_out';
                  const badgeClass = isPassing ? 'b-green' : isFailed ? 'b-red' : 'b-amber';

                  return (
                    <tr key={row.id}>
                      <td>#{row.id}</td>
                      <td style={{ fontFamily: 'monospace', fontSize: '11px' }}>
                        <Link to={`/alphas/${row.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>{row.expression}</Link>
                      </td>
                      <td>{row.theme}</td>
                      <td>{formatNumber(row.sharpe, 2)}</td>
                      <td>{formatNumber(row.fitness, 2)}</td>
                      <td>{formatPercent(row.turnover, 1)}</td>
                      <td>
                        <span className={`badge ${badgeClass}`}>{formatLabel(statusStr)}</span>
                        {row.needs_review ? <span className="badge b-amber" style={{ marginLeft: '4px' }}>Review Required</span> : null}
                        {row.simulation_failed ? <p className="cell-note" style={{ color: 'var(--color-text-danger)' }}>{row.failure_note}</p> : null}
                        {row.status === 'screened_out' && row.pre_backtest_score != null ? (
                          <p className="cell-note">Local backtest score {formatNumber(row.pre_backtest_score, 2)}</p>
                        ) : null}
                        {!row.simulation_failed && row.gate_failure_reason ? <p className="cell-note" style={{ color: 'var(--color-text-warning)' }}>{row.gate_failure_reason}</p> : null}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState message="No alphas matched the current filters." />
        )}
      </Panel>

      <div style={{ marginTop: '12px' }}>
        <Panel title="Correlation Snapshot" subtitle="Token-overlap proxy across recent alphas">
          {state.data?.correlation_matrix?.length ? (
            <div style={{ overflowX: 'auto' }}>
              <table className="tbl-layout">
                <thead>
                  <tr>
                    {Object.keys(state.data.correlation_matrix[0]).map((key) => (
                      <th key={key}>{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {state.data.correlation_matrix.map((row, index) => (
                    <tr key={`matrix-${index}`}>
                      {Object.entries(row).map(([key, value]) => (
                        <td key={key}>{String(value)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState message="Not enough recent alphas for a similarity matrix." />
          )}
        </Panel>
      </div>
    </div>
  )
}

function AlphaDetailPage() {
  const params = useParams()
  const [tab, setTab] = useState<'reasoning' | 'research' | 'checks' | 'log'>('reasoning')
  const state = usePolling<AlphaDetailResponse>(() => api.getAlphaDetail(String(params.alphaId)), [params.alphaId], 15000)

  if (state.loading && !state.data) return <LoadingState message="Loading alpha detail…" />
  if (state.error && !state.data) return <ErrorState message={state.error} />
  if (!state.data) return <EmptyState message="Alpha detail unavailable." />

  const alpha = state.data.alpha
  return (
    <div style={{ padding: '0 4px' }}>
      <Panel title="Alpha Detail" subtitle={`Alpha #${String(alpha.id)}`}>
        <div style={{ padding: '8px 0 16px 0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '0.5px solid var(--color-border-tertiary)', marginBottom: '16px' }}>
          <div style={{ fontFamily: 'monospace', fontSize: '14px', color: 'var(--color-text-primary)', background: 'var(--color-background-tertiary)', padding: '10px 14px', borderRadius: '6px', border: '0.5px solid var(--color-border-tertiary)', flex: 1, marginRight: '16px', overflowX: 'auto' }}>
            {alpha.expression}
          </div>
          <div style={{ display: 'flex', gap: '6px', flexShrink: 0 }}>
            <span className={`badge ${alpha.simulation_failed ? 'b-red' : (alpha.status === 'approved' || alpha.status === 'submitted' || alpha.sharpe >= 2.0) ? 'b-green' : 'b-amber'}`}>
              {formatLabel(alpha.simulation_failed ? 'failed' : alpha.status)}
            </span>
            {alpha.needs_review ? <span className="badge b-amber">Review Required</span> : null}
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="card" style={{ display: 'flex', gap: '12px', padding: '12px', marginBottom: '12px', border: 'none', background: 'var(--color-background-secondary)' }}>
          <div className="metric-widget" style={{ flex: 1 }}>
            <div className="metric-label">Sharpe</div>
            <div className="metric-val">{formatNumber(alpha.sharpe, 2)}</div>
            <div className="metric-sub">Pass target &ge; 1.0</div>
          </div>
          <div className="metric-widget" style={{ flex: 1 }}>
            <div className="metric-label">Fitness</div>
            <div className="metric-val">{formatNumber(alpha.fitness, 2)}</div>
            <div className="metric-sub">Signal efficiency</div>
          </div>
          <div className="metric-widget" style={{ flex: 1 }}>
            <div className="metric-label">Turnover</div>
            <div className="metric-val">{formatPercent(alpha.turnover, 1)}</div>
            <div className="metric-sub">Execution intensity</div>
          </div>
          <div className="metric-widget" style={{ flex: 1 }}>
            <div className="metric-label">Returns</div>
            <div className="metric-val">{formatPercent(alpha.annual_returns, 1)}</div>
            <div className="metric-sub">Annualized proxy</div>
          </div>
          <div className="metric-widget" style={{ flex: 1 }}>
            <div className="metric-label">Local Backtest</div>
            <div className="metric-val">
              {alpha.pre_backtest_score != null ? formatNumber(alpha.pre_backtest_score, 2) : 'n/a'}
            </div>
            <div className="metric-sub">{alpha.pre_backtest_passed ? 'Passed proxy gate' : 'Blocked/no run'}</div>
          </div>
        </div>

        {alpha.gate_failure_reason ? (
          <div style={{ padding: '10px 12px', borderRadius: '6px', background: '#FFF7ED', border: '0.5px solid #FFEDD5', color: '#C2410C', fontSize: '12px', marginBottom: '12px' }}>
            <strong>Gate failure reason:</strong> {alpha.gate_failure_reason}
          </div>
        ) : null}
        {alpha.simulation_failed && alpha.failure_note ? (
          <div style={{ padding: '10px 12px', borderRadius: '6px', background: '#FEF2F2', border: '0.5px solid #FEE2E2', color: '#B91C1C', fontSize: '12px', marginBottom: '12px' }}>
            <strong>Simulation error:</strong> {alpha.failure_note}
          </div>
        ) : null}
      </Panel>

      <Panel title="Explainability" subtitle={state.data.features.theme}>
        <div className="tab-strip">
          {[
            ['reasoning', 'Agent Reasoning'],
            ['research', 'Research Basis'],
            ['checks', 'Brain Checks'],
            ['log', 'Raw Log'],
          ].map(([key, label]) => (
            <button key={key} className={`tab-button ${tab === key ? 'active' : ''}`} onClick={() => setTab(key as typeof tab)}>
              {label}
            </button>
          ))}
        </div>

        {tab === 'reasoning' ? (
          <div className="stack-block">
            <article className="detail-card">
              <p className="eyebrow">Why This Alpha Was Created</p>
              <h3>{state.data.features.theme}</h3>
              <p>{state.data.analysis.creation_reason}</p>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Hypothesis</p>
              <h3>{state.data.explanation.hypothesis}</h3>
              <p>{state.data.explanation.prompt_context || 'No stored prompt context for this alpha.'}</p>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Generation Telemetry</p>
              <div className="key-grid">
                <div>
                  <span>Generation source</span>
                  <strong>{String(alpha.generation_source ?? alpha.source ?? 'unknown')}</strong>
                </div>
                <div>
                  <span>Origin agent</span>
                  <strong>{String(alpha.origin_agent ?? 'n/a')}</strong>
                </div>
                <div>
                  <span>Pre-review</span>
                  <strong>
                    {String(alpha.pre_sim_verdict ?? 'n/a')}
                    {alpha.pre_sim_confidence != null ? ` · ${formatNumber(alpha.pre_sim_confidence)}` : ''}
                  </strong>
                </div>
                <div>
                  <span>Post-review</span>
                  <strong>
                    {String(alpha.post_sim_verdict ?? 'n/a')}
                    {alpha.post_sim_confidence != null ? ` · ${formatNumber(alpha.post_sim_confidence)}` : ''}
                  </strong>
                </div>
              </div>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Local Backtest Gate</p>
              <div className="key-grid">
                <div>
                  <span>Composite score</span>
                  <strong>{alpha.pre_backtest_score != null ? formatNumber(alpha.pre_backtest_score) : 'n/a'}</strong>
                </div>
                <div>
                  <span>Promoted</span>
                  <strong>{alpha.pre_backtest_passed ? 'yes' : 'no'}</strong>
                </div>
                <div>
                  <span>Proxy Sharpe</span>
                  <strong>{formatNumber(alpha.pre_backtest_metrics?.sharpe)}</strong>
                </div>
                <div>
                  <span>Proxy Fitness</span>
                  <strong>{formatNumber(alpha.pre_backtest_metrics?.fitness)}</strong>
                </div>
              </div>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Evidence And Basis</p>
              <ul className="flat-list">
                {state.data.analysis.evidence_basis.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Theory Basis</p>
              <ul className="flat-list">
                {state.data.analysis.theory_basis.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Implementation Logic</p>
              <ul className="flat-list">
                {state.data.analysis.implementation_logic.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Expected Metrics</p>
              <div className="key-grid">
                {Object.entries(state.data.explanation.expected_metrics).map(([key, value]) => (
                  <div key={key}>
                    <span>{key}</span>
                    <strong>{String(value)}</strong>
                  </div>
                ))}
              </div>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Risk Notes</p>
              <ul className="flat-list">
                {state.data.analysis.confidence_notes.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Agent Reviews</p>
              {Array.isArray(state.data.explanation.agent_reviews) && state.data.explanation.agent_reviews.length ? (
                <div className="review-list">
                  {state.data.explanation.agent_reviews.map((review, index) => (
                    <div key={`review-${index}`} className="review-card">
                      <strong>{String(review.agent ?? 'agent')} · {String(review.stage ?? 'stage')} · {String(review.verdict ?? 'WARN')}</strong>
                      <p>{String(review.summary ?? '')}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState message="No persisted agent review for this alpha." />
              )}
            </article>
          </div>
        ) : null}

        {tab === 'research' ? (
          <div className="stack-block">
            <article className="detail-card">
              <p className="eyebrow">Matched Theories</p>
              <div className="theory-inline-list">
                {state.data.matched_theories.map((theory) => (
                  <div key={theory.id} className="theory-inline-card">
                    <strong>{theory.title}</strong>
                    <p>{theory.core_principle}</p>
                    <ExpressionCode expression={theory.example_expression} />
                  </div>
                ))}
              </div>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Data Fields</p>
              <div className="key-grid">
                {state.data.field_info.map((item, index) => (
                  <div key={`field-${index}`}>
                    <span>{String(item.field)}</span>
                    <strong>{String(item.description)}</strong>
                  </div>
                ))}
              </div>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Operators</p>
              <div className="key-grid">
                {state.data.operator_info.map((item, index) => (
                  <div key={`op-${index}`}>
                    <span>{String(item.operator)}</span>
                    <strong>{String(item.definition)}</strong>
                  </div>
                ))}
              </div>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Related Documents</p>
              {state.data.related_documents.length ? (
                state.data.related_documents.map((doc) => (
                  <div key={doc.path} className="doc-card">
                    <strong>{doc.path}</strong>
                    <p>{doc.excerpt}</p>
                  </div>
                ))
              ) : (
                <EmptyState message="No related documents were found." />
              )}
            </article>
          </div>
        ) : null}

        {tab === 'checks' ? (
          <div className="stack-block">
            {Array.isArray(state.data.checks) && state.data.checks.length ? (
              state.data.checks.map((check, index) => (
                <article key={`check-${index}`} className="detail-card">
                  <strong>{String(check.name ?? `Check ${index + 1}`)}</strong>
                  <p>{String(check.message ?? JSON.stringify(check))}</p>
                </article>
              ))
            ) : (
              <article className="detail-card">
                <p>No structured checks were stored for this alpha. Use the raw metrics above as the current evaluation snapshot.</p>
              </article>
            )}
          </div>
        ) : null}

        {tab === 'log' ? (
          <div className="stack-block">
            <article className="detail-card">
              <p className="eyebrow">Notes</p>
              <p>{String(alpha.notes ?? 'No stored notes.')}</p>
            </article>
            <article className="detail-card">
              <p className="eyebrow">Research Artifacts</p>
              {state.data.research.length ? (
                state.data.research.map((artifact) => (
                  <div key={artifact.id} className="doc-card">
                    <strong>{artifact.title}</strong>
                    <p>{artifact.content}</p>
                  </div>
                ))
              ) : (
                <EmptyState message="No run-linked research artifact found." />
              )}
            </article>
          </div>
        ) : null}
      </Panel>
    </div>
  )
}

function ResearchPage() {
  const runsState = usePolling(() => api.getPipelineRuns(20), [], 10000)
  const [runId, setRunId] = useState('')
  const activeRunId = runId || runsState.data?.items?.[0]?.run_id || ''
  const researchState = usePolling(() => api.getResearch(activeRunId || undefined), [activeRunId], 15000)

  if (researchState.loading && !researchState.data) return <LoadingState message="Loading research context…" />
  if (researchState.error && !researchState.data) return <ErrorState message={researchState.error} />
  const mapping = (researchState.data?.mapping ?? []) as Array<Record<string, unknown>>

  return (
    <div className="page-grid">
      <Panel title="Research Context" subtitle="How DeerFlow context flowed into alpha creation">
        <div className="filter-grid">
          <select value={runId} onChange={(event) => setRunId(event.target.value)}>
            <option value="">Latest run</option>
            {(runsState.data?.items ?? []).map((run: PipelineRun) => (
              <option key={run.run_id} value={run.run_id}>
                {run.run_id} · {run.workflow_type}
              </option>
            ))}
          </select>
        </div>

        {mapping.length ? (
          <div className="research-list">
            {mapping.map((item) => (
              <article key={String(item.artifact_id)} className="research-card">
                <div className="research-head">
                  <strong>{String(item.title)}</strong>
                  <span>{String(item.kind)}</span>
                </div>
                <p>{String(item.query_text ?? '')}</p>
                <p>{String(item.content).slice(0, 900)}</p>
                <div className="research-links">
                  <span>Influence score: {String(item.influence_score)}%</span>
                  <span>Mapped alphas: {Array.isArray(item.related_alphas) ? item.related_alphas.length : 0}</span>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <EmptyState message="No research mapping found for the selected run." />
        )}
      </Panel>

      <Panel title="Recent Knowledge Files" subtitle="Newest documents in the local research base">
        {Array.isArray(researchState.data?.recent_files) && researchState.data?.recent_files.length ? (
          <div className="doc-list">
            {(researchState.data?.recent_files as string[]).map((path) => (
              <div key={path} className="doc-card">
                <strong>{path}</strong>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState message="No recent research files found." />
        )}
      </Panel>
    </div>
  )
}

function LogsPage() {
  const [selectedPath, setSelectedPath] = useState('')
  const state = usePolling(() => api.getLogs(selectedPath || undefined), [selectedPath], 5000)

  if (state.loading && !state.data) return <LoadingState message="Loading logs…" />
  if (state.error && !state.data) return <ErrorState message={state.error} />
  const events = (state.data?.events ?? []) as PipelineEvent[]
  const tail = (state.data?.tail ?? []) as string[]

  return (
    <div className="page-grid">
      <Panel title="Simulation Log" subtitle="Event stream and raw tails">
        <div className="filter-grid">
          <select value={selectedPath} onChange={(event) => setSelectedPath(event.target.value)}>
            <option value="">Primary log</option>
            {((state.data?.available_files ?? []) as string[]).map((path) => (
              <option key={path} value={path}>
                {path}
              </option>
            ))}
          </select>
        </div>
        <div className="log-columns">
          <div className="log-panel">
            <p className="eyebrow">Workflow events</p>
            {events.length ? (
              events.map((event) => (
                <div key={event.id} className="feed-item">
                  <span>{event.created_at.slice(11, 19)}</span>
                  <strong>{event.event_type}</strong>
                  <p>{event.message}</p>
                </div>
              ))
            ) : (
              <EmptyState message="No workflow events available." />
            )}
          </div>
          <div className="log-panel">
            <p className="eyebrow">Raw file tail</p>
            <pre className="code-block">{tail.join('\n')}</pre>
          </div>
        </div>
      </Panel>
    </div>
  )
}

function SettingsPage({ options }: { options: OptionsResponse | null }) {
  const state = usePolling<SettingsResponse>(() => api.getSettings(), [], 0)
  const [form, setForm] = useState<Record<string, unknown> | null>(null)
  const [initialForm, setInitialForm] = useState<Record<string, unknown> | null>(null)
  const [revealed, setRevealed] = useState<Record<string, boolean>>({
    worldquant_password: false,
    openrouter_api_key: false,
  })
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!state.data || form) return
    const loaded = state.data
    const timer = window.setTimeout(() => {
      const nextForm = {
        worldquant_username: loaded.credentials.worldquant_username,
        worldquant_password: '',
        openrouter_api_key: '',
        alphas_per_run: loaded.pipeline.alphas_per_run,
        region: loaded.pipeline.region,
        universe: loaded.pipeline.universe,
        neutralization: loaded.pipeline.neutralization,
        auto_submit: loaded.pipeline.auto_submit,
        sim_throttle: loaded.pipeline.sim_throttle,
        max_daily_submissions: loaded.pipeline.max_daily_submissions,
        self_critique_rounds: loaded.ai.self_critique_rounds,
        enable_research: loaded.ai.enable_research,
        custom_research_prompt: loaded.ai.custom_research_prompt,
      }
      setForm(nextForm)
      setInitialForm(nextForm)
    }, 0)
    return () => window.clearTimeout(timer)
  }, [form, state.data])

  if (state.loading && !state.data) return <LoadingState message="Loading settings…" />
  if (state.error && !state.data) return <ErrorState message={state.error} />
  if (!form || !state.data) return <EmptyState message="Settings unavailable." />

  const update = (key: string, value: unknown) => setForm((current) => ({ ...(current ?? {}), [key]: value }))
  const toggleReveal = (key: string) => setRevealed((current) => ({ ...current, [key]: !current[key] }))
  const buildDirtyPayload = () => {
    const dirty: Record<string, unknown> = {}
    Object.entries(form).forEach(([key, value]) => {
      const initialValue = initialForm?.[key]
      if (JSON.stringify(initialValue) === JSON.stringify(value)) return
      if ((key === 'worldquant_password' || key === 'openrouter_api_key') && value === '') return
      dirty[key] = value
    })
    return dirty
  }

  const save = async () => {
    try {
      const dirty = buildDirtyPayload()
      if (!Object.keys(dirty).length) {
        setMessage('No settings changed.')
        return
      }
      const result = await api.saveSettings(dirty)
      setMessage(result.message)
      const nextForm = {
        ...form,
        worldquant_password: '',
        openrouter_api_key: '',
      }
      setForm(nextForm)
      setInitialForm(nextForm)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Failed to save settings')
    }
  }

  const testWorldQuantConnection = async () => {
    try {
      const result = await api.testSettingsConnection({
        provider: 'worldquant',
        worldquant_username: form.worldquant_username,
        worldquant_password: form.worldquant_password,
      })
      setMessage(result.message)
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'WorldQuant connection test failed')
    }
  }

  return (
    <div className="page-grid">
      <Panel title="Settings" subtitle="Credentials, pipeline defaults, and AI behavior">
        {message ? <div className="toast inline">{message}</div> : null}
        <div className="settings-grid">
          <div className="detail-card">
            <p className="eyebrow">Credentials</p>
            <label>
              WorldQuant username
              <input value={String(form.worldquant_username ?? '')} onChange={(event) => update('worldquant_username', event.target.value)} />
            </label>
            <CredentialInput
              label="WorldQuant password"
              placeholder={state.data.credentials.worldquant_password_masked}
              value={String(form.worldquant_password ?? '')}
              revealed={Boolean(revealed.worldquant_password)}
              onToggle={() => toggleReveal('worldquant_password')}
              onChange={(value) => update('worldquant_password', value)}
              onTest={testWorldQuantConnection}
            />
            <CredentialInput
              label="OpenRouter API key"
              placeholder={state.data.credentials.openrouter_api_key_masked}
              value={String(form.openrouter_api_key ?? '')}
              revealed={Boolean(revealed.openrouter_api_key)}
              onToggle={() => toggleReveal('openrouter_api_key')}
              onChange={(value) => update('openrouter_api_key', value)}
            />
          </div>

          <div className="detail-card">
            <p className="eyebrow">Pipeline</p>
            <label>
              Alphas per run
              <input type="number" value={String(form.alphas_per_run ?? 10)} onChange={(event) => update('alphas_per_run', Number(event.target.value))} />
            </label>
            <label>
              Region
              <input value={String(form.region ?? 'USA')} onChange={(event) => update('region', event.target.value)} />
            </label>
            <label>
              Universe
              <select value={String(form.universe ?? 'TOP3000')} onChange={(event) => update('universe', event.target.value)}>
                {(options?.universe_options ?? []).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Neutralization
              <select value={String(form.neutralization ?? 'SUBINDUSTRY')} onChange={(event) => update('neutralization', event.target.value)}>
                {(options?.neutralization_options ?? []).map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="checkbox-row">
              <input type="checkbox" checked={Boolean(form.auto_submit)} onChange={(event) => update('auto_submit', event.target.checked)} />
              Auto-submit passing alpha
            </label>
          </div>

          <div className="detail-card">
            <p className="eyebrow">AI Config</p>
            <label>
              Sim throttle (seconds)
              <input type="number" value={String(form.sim_throttle ?? 5)} onChange={(event) => update('sim_throttle', Number(event.target.value))} />
            </label>
            <label>
              Max daily submissions
              <input
                type="number"
                value={String(form.max_daily_submissions ?? 1)}
                onChange={(event) => update('max_daily_submissions', Number(event.target.value))}
              />
            </label>
            <label>
              Self-critique rounds
              <input
                type="number"
                value={String(form.self_critique_rounds ?? 2)}
                onChange={(event) => update('self_critique_rounds', Number(event.target.value))}
              />
            </label>
            <label className="checkbox-row">
              <input type="checkbox" checked={Boolean(form.enable_research)} onChange={(event) => update('enable_research', event.target.checked)} />
              Enable research
            </label>
            <label>
              Custom research prompt
              <textarea
                rows={4}
                value={String(form.custom_research_prompt ?? '')}
                onChange={(event) => update('custom_research_prompt', event.target.value)}
              />
            </label>
          </div>
        </div>
        <div className="panel-actions">
          <button className="ghost-button" onClick={() => void save()}>
            Save settings
          </button>
        </div>
      </Panel>
    </div>
  )
}

function TheoriesPage({ options }: { options: OptionsResponse | null }) {
  const [domain, setDomain] = useState('')
  const [sector, setSector] = useState('')
  const [search, setSearch] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [message, setMessage] = useState('')
  const [form, setForm] = useState({
    theory_id: '',
    domain: 'Economics',
    title: '',
    sector_tags: '',
    core_principle: '',
    alpha_implication: '',
    example_expression: '',
    agent_reasoning: '',
    source: 'ui',
    created_by: 'user',
    status: 'active',
  })
  const state = usePolling(() => api.getTheories({ domain, sector, search }), [domain, sector, search], 0)
  const usageState = usePolling<TheoryUsageResponse>(() => api.getTheoryUsage(400), [], 15000)
  const usageMap = new Map((usageState.data?.items ?? []).map((item) => [item.theory_id, item]))

  const saveTheory = async () => {
    try {
      const payload = {
        ...form,
        sector_tags: form.sector_tags.split(',').map((item) => item.trim()).filter(Boolean),
        alpha_implication: form.alpha_implication.split('\n').map((item) => item.trim()).filter(Boolean),
        agent_reasoning: form.agent_reasoning.split('\n').map((item) => item.trim()).filter(Boolean),
      }
      await api.saveTheory(payload)
      setMessage(`Saved theory ${form.theory_id}`)
      setShowForm(false)
      void state.refetch()
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Failed to save theory')
    }
  }

  return (
    <div className="page-grid">
      <Panel
        title="Theory Explorer"
        subtitle="22+ theories mapped to alpha design and agent reasoning"
        actions={<button className="ghost-button" onClick={() => setShowForm((current) => !current)}>{showForm ? 'Close form' : 'Add theory'}</button>}
      >
        {message ? <div className="toast inline">{message}</div> : null}
        {usageState.data ? (
          <div className="metrics-grid">
            <MetricCard
              label="Tracked theories"
              value={String(usageState.data.summary.tracked_theories)}
              detail={`${usageState.data.summary.used_theories} have generated alpha links`}
            />
            <MetricCard
              label="Unused"
              value={String(usageState.data.summary.unused_theories)}
              detail="Theories with no linked alpha generation yet"
            />
            <MetricCard
              label="Top pass rate"
              value={usageState.data.top[0] ? formatPercent(usageState.data.top[0].pass_rate) : '0%'}
              detail={usageState.data.top[0] ? usageState.data.top[0].title : 'No linked theories yet'}
            />
            <MetricCard
              label="Top generated"
              value={usageState.data.top[0] ? String(usageState.data.top[0].generated) : '0'}
              detail="Most frequently linked theory"
            />
          </div>
        ) : null}
        <div className="filter-grid">
          <select value={domain} onChange={(event) => setDomain(event.target.value)}>
            <option value="">All domains</option>
            {(options?.theory_domains ?? []).map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <select value={sector} onChange={(event) => setSector(event.target.value)}>
            <option value="">All sectors</option>
            {(options?.theory_sectors ?? []).map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search theory, field, or expression" />
        </div>

        {showForm ? (
          <div className="detail-card form-card">
            <div className="settings-grid">
              <label>
                Theory id
                <input value={form.theory_id} onChange={(event) => setForm({ ...form, theory_id: event.target.value })} />
              </label>
              <label>
                Domain
                <select value={form.domain} onChange={(event) => setForm({ ...form, domain: event.target.value })}>
                  {(options?.theory_domains ?? []).map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Title
                <input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} />
              </label>
              <label>
                Sector tags
                <input value={form.sector_tags} onChange={(event) => setForm({ ...form, sector_tags: event.target.value })} placeholder="Comma-separated" />
              </label>
            </div>
            <label>
              Core principle
              <textarea rows={3} value={form.core_principle} onChange={(event) => setForm({ ...form, core_principle: event.target.value })} />
            </label>
            <label>
              Alpha implications
              <textarea rows={3} value={form.alpha_implication} onChange={(event) => setForm({ ...form, alpha_implication: event.target.value })} />
            </label>
            <label>
              Example expression
              <input value={form.example_expression} onChange={(event) => setForm({ ...form, example_expression: event.target.value })} />
            </label>
            <label>
              Agent reasoning chain
              <textarea rows={4} value={form.agent_reasoning} onChange={(event) => setForm({ ...form, agent_reasoning: event.target.value })} />
            </label>
            <div className="panel-actions">
              <button className="ghost-button" onClick={() => void saveTheory()}>
                Save theory
              </button>
            </div>
          </div>
        ) : null}

        {state.loading && !state.data ? <LoadingState message="Loading theories…" /> : null}
        {state.error && !state.data ? <ErrorState message={state.error} /> : null}

        <div className="theory-grid">
          {(state.data?.items ?? []).map((theory: TheoryEntry) => {
            const open = expanded === theory.id
            const usage = usageMap.get(theory.id)
            return (
              <article key={theory.id} className={`theory-card ${open ? 'open' : ''}`}>
                <button className="theory-toggle" onClick={() => setExpanded(open ? null : theory.id)}>
                  <div>
                    <p className="eyebrow">{theory.domain}</p>
                    <h3>{theory.title}</h3>
                  </div>
                  <span>{open ? '−' : '+'}</span>
                </button>
                <div className="tag-row">
                  {theory.sector_tags.map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                    </span>
                  ))}
                </div>
                <div className="theory-usage-strip">
                  <span>Generated {String(usage?.generated ?? 0)}</span>
                  <span>Pass rate {formatPercent(usage?.pass_rate ?? 0)}</span>
                  <span>Avg Sharpe {formatNumber(usage?.avg_sharpe ?? 0)}</span>
                </div>
                {open ? (
                  <div className="stack-block">
                    <div className="detail-card">
                      <p className="eyebrow">Core principle</p>
                      <p>{theory.core_principle}</p>
                    </div>
                    <div className="detail-card">
                      <p className="eyebrow">Alpha implication</p>
                      <ul className="flat-list">
                        {theory.alpha_implication.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="detail-card">
                      <p className="eyebrow">Sample expression</p>
                      <ExpressionCode expression={theory.example_expression} />
                    </div>
                    <div className="detail-card">
                      <p className="eyebrow">Agent reasoning chain</p>
                      <ul className="flat-list">
                        {theory.agent_reasoning.map((item) => (
                          <li key={item}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ) : null}
              </article>
            )
          })}
        </div>
      </Panel>
    </div>
  )
}

function StudioPage({
  options,
  overview,
  onInspectAlpha,
}: {
  options: OptionsResponse | null
  overview: OverviewResponse | null
  onInspectAlpha: (id: number) => void
}) {
  const runsState = usePolling(() => api.getPipelineRuns(6), [], 5000)
  const latestRunId = runsState.data?.items?.[0]?.run_id ?? ''
  const eventsState = usePolling(
    () => (latestRunId ? api.getPipelineRunEvents(latestRunId, 18) : Promise.resolve({ items: [] as PipelineEvent[] })),
    [latestRunId],
    5000,
  )
  const [strategyType, setStrategyType] = useState('momentum')
  const [focusQuery, setFocusQuery] = useState('improve fitness over 1')
  const [target] = useState('DeerFlow')
  const [objective, setObjective] = useState('Fitness-first')
  const [count, setCount] = useState(8)
  const [prompt, setPrompt] = useState('Research how to improve fitness over 1 in WorldQuant alpha generation before creating new signals.')
  const [chatInput, setChatInput] = useState('DeerFlow, critique the current alpha direction and suggest the next best improvement.')
  const [manualExpression, setManualExpression] = useState('')
  const [contextBundle, setContextBundle] = useState<Record<string, string> | null>(null)
  const [responses, setResponses] = useState<Record<string, unknown> | null>(null)
  const [candidatePool, setCandidatePool] = useState<StudioCandidate[]>([])
  const [chatMessages, setChatMessages] = useState<StudioChatMessage[]>([])
  const [selectedExpression, setSelectedExpression] = useState('')
  const [simulation, setSimulation] = useState<Record<string, unknown> | null>(null)
  const [busy, setBusy] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    void api.getChatMessages('studio', 60).then((res) => {
      const items = (res.items ?? []).map((m: Record<string, unknown>) => ({
        id: String(m.id ?? ''),
        role: String(m.role ?? 'user') as 'user' | 'agent' | 'system',
        agent: String(m.agent ?? ''),
        content: String(m.content ?? ''),
        createdAt: String(m.created_at ?? ''),
      }))
      setChatMessages(items)
    }).catch(() => {})
  }, [])

  const pushChatMessages = (nextMessages: StudioChatMessage[]) => {
    setChatMessages((current) => [...current, ...nextMessages])
  }

  const recordConversation = (userPrompt: string, payload: Record<string, string>) => {
    const stamp = new Date().toISOString()
    const allMsgs: StudioChatMessage[] = [
      {
        id: `${stamp}-user`,
        role: 'user',
        agent: target,
        content: userPrompt,
        createdAt: stamp,
      },
      ...Object.entries(payload).map(([agent, text], index) => ({
        id: `${stamp}-${agent}-${index}`,
        role: 'agent' as const,
        agent,
        content: text,
        createdAt: stamp,
      })),
    ]
    pushChatMessages(allMsgs)
    for (const msg of allMsgs) {
      void api.postChatMessage({ session: 'studio', role: msg.role, agent: msg.agent, content: msg.content }).catch(() => {})
    }
  }

  const mergeCandidates = (payload: Record<string, unknown>) => {
    const next = [...candidatePool]
    const seen = new Set(candidatePool.map((item) => item.expression.replace(/\s+/g, '')))
    Object.entries(payload).forEach(([source, items]) => {
      if (!Array.isArray(items)) return
      items.forEach((item) => {
        const candidate = item as StudioCandidate
        const key = candidate.expression.replace(/\s+/g, '')
        if (seen.has(key)) return
        seen.add(key)
        next.push({ ...candidate, source })
      })
    })
    setCandidatePool(next)
    if (!selectedExpression && next[0]) setSelectedExpression(next[0].expression)
  }

  const loadContext = async () => {
    setBusy('context')
    try {
      const result = await api.getStudioContext({ strategy_type: strategyType, focus_query: focusQuery })
      setContextBundle(result)
      setMessage('Context bundle refreshed.')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Failed to load context.')
    } finally {
      setBusy('')
    }
  }

  const runQuery = async () => {
    setBusy('query')
    try {
      const result = await api.studioQuery({ target, prompt })
      setResponses(result)
      mergeCandidates((result.extracted ?? {}) as Record<string, unknown>)
      recordConversation(prompt, (result.responses ?? {}) as Record<string, string>)
      setMessage('Agent responses received.')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Failed to query agents.')
    } finally {
      setBusy('')
    }
  }

  const runGenerate = async () => {
    setBusy('generate')
    try {
      const result = await api.studioGenerate({
        target,
        strategy_type: strategyType,
        objective,
        count,
        context: contextBundle?.context ?? '',
      })
      setResponses(result)
      mergeCandidates((result.extracted ?? {}) as Record<string, unknown>)
      pushChatMessages([
        {
          id: `${Date.now()}-system-generate`,
          role: 'system',
          agent: 'Studio',
          content: `Generated alpha pack for ${strategyType} with objective ${objective}.`,
          createdAt: new Date().toISOString(),
        },
      ])
      setMessage('Alpha pack generated.')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Failed to generate alpha pack.')
    } finally {
      setBusy('')
    }
  }

  const runSimulate = async () => {
    const expression = selectedExpression || manualExpression
    const selectedCandidate = candidatePool.find((item) => item.expression === expression)
    if (!expression) {
      setMessage('Pick or type an expression first.')
      return
    }
    setBusy('simulate')
    try {
      const result = await api.studioSimulate({
        expression,
        strategy_type: strategyType,
        metadata: {
          region: 'USA',
          universe: 'TOP3000',
          neutralization: 'SUBINDUSTRY',
          generation_source: selectedCandidate?.source ? `${selectedCandidate.source.toLowerCase()}_studio` : 'studio_manual',
          origin_agent: selectedCandidate?.source ?? 'Studio',
        },
        review_context: contextBundle?.context ?? '',
      })
      setSimulation(result)
      const alphaRunId = Number(result.alpha_run_id ?? 0)
      if (alphaRunId) {
        setMessage(`Simulation stored as alpha #${alphaRunId}.`)
      } else {
        setMessage('Simulation completed.')
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Failed to simulate candidate.')
    } finally {
      setBusy('')
    }
  }

  const sendChat = async () => {
    const messageText = chatInput.trim()
    if (!messageText) {
      setMessage('Type a message before sending it to the agents.')
      return
    }
    setBusy('chat')
    try {
      const result = await api.studioQuery({ target, prompt: messageText })
      setResponses(result)
      mergeCandidates((result.extracted ?? {}) as Record<string, unknown>)
      recordConversation(messageText, (result.responses ?? {}) as Record<string, string>)
      setChatInput('')
      setMessage('Chatspace updated with fresh agent replies.')
    } catch (err) {
      setMessage(err instanceof Error ? err.message : 'Failed to send chat message.')
    } finally {
      setBusy('')
    }
  }

  const activeAgents = target === 'Both' ? ['Hermes', 'DeerFlow'] : [target]
  const latestEvents = (eventsState.data?.items ?? []) as PipelineEvent[]
  const recentRuns = (runsState.data?.items ?? []) as PipelineRun[]
  const selectedCandidate = candidatePool.find((item) => item.expression === selectedExpression)
  const validCandidateCount = candidatePool.filter((item) => item.valid).length
  const workflowSteps: WorkflowStep[] = [
    {
      label: 'Brief',
      detail: contextBundle ? 'Research context is loaded' : 'Refresh context before asking agents',
      status: busy === 'context' ? 'active' : contextBundle ? 'done' : 'idle',
    },
    {
      label: 'Collaborate',
      detail: responses ? 'Agent feedback is available' : 'Ask agents or use chatspace',
      status: ['query', 'generate', 'chat'].includes(busy) ? 'active' : responses ? 'done' : contextBundle ? 'idle' : 'blocked',
    },
    {
      label: 'Select',
      detail: candidatePool.length ? `${validCandidateCount}/${candidatePool.length} candidates are valid` : 'No candidates collected yet',
      status: selectedExpression ? 'done' : candidatePool.length ? 'active' : 'blocked',
    },
    {
      label: 'Simulate',
      detail: simulation ? 'Simulation result is ready' : selectedExpression ? 'Ready to simulate selected alpha' : 'Pick an expression first',
      status: busy === 'simulate' ? 'active' : simulation ? 'done' : selectedExpression ? 'idle' : 'blocked',
    },
  ]
  const agentLanes = ['DeerFlow'].map((agent) => {
    const touchedInChat = chatMessages.some((item) => item.agent === agent && item.role === 'agent')
    const thinking = ['query', 'generate', 'chat'].includes(busy) && activeAgents.includes(agent)
    return {
      name: agent,
      status: thinking ? 'running' : touchedInChat ? 'done' : 'idle',
      detail: thinking ? 'Working on the latest request' : touchedInChat ? 'Has replied in this session' : 'Waiting for input',
    }
  })

  return (
    <div className="page-grid">
      <Panel title="Studio Command Center" subtitle="Move from research brief to simulated alpha without losing your place">
        {message ? <div className="toast inline">{message}</div> : null}
        <div className="studio-command-shell">
          <div className="studio-hero-card">
            <p className="eyebrow">Current mission</p>
            <h3>{strategyType} / {objective}</h3>
            <p>
              Work the loop from left to right: load context, collaborate with agents, choose a candidate, then simulate. The Studio will keep the
              active candidate and latest result visible while the workflow moves.
            </p>
            <div className="mission-tags">
              <span className="tag">Target: {target}</span>
              <span className="tag">{count} requested</span>
              <span className="tag">{candidatePool.length} collected</span>
              {selectedCandidate ? <span className="tag">Selected: {selectedCandidate.source}</span> : null}
            </div>
          </div>
          <WorkflowStepRail steps={workflowSteps} />
        </div>
        <div className="command-grid">
          <CommandCard
            title="1. Context"
            detail={contextBundle ? 'Context bundle refreshed' : 'Load relevant research and lessons'}
            actionLabel={busy === 'context' ? 'Refreshing...' : 'Refresh context'}
            disabled={busy !== ''}
            tone="primary"
            onAction={() => void loadContext()}
          />
          <CommandCard
            title="2. Generate"
            detail={responses ? 'Agent output is ready to review' : 'Ask agents for candidates'}
            actionLabel={busy === 'generate' ? 'Generating...' : 'Generate pack'}
            disabled={busy !== ''}
            onAction={() => void runGenerate()}
          />
          <CommandCard
            title="3. Simulate"
            detail={selectedExpression ? 'Selected candidate is ready' : 'Select or add a candidate first'}
            actionLabel={busy === 'simulate' ? 'Simulating...' : 'Simulate selected'}
            disabled={busy !== '' || !selectedExpression}
            onAction={() => void runSimulate()}
          />
        </div>
      </Panel>

      <Panel title="Workflow Tracker" subtitle="See where agents and the active workflow are right now">
        <div className="tracker-shell">
          <div className="tracker-summary">
            <div className="detail-card">
              <p className="eyebrow">Active workflow</p>
              <strong>{latestRunId || 'No tracked run'}</strong>
              <p className="muted">
                {overview?.latest_run
                  ? `${formatLabel(String(overview.latest_run.workflow_type))} · ${formatLabel(String(overview.latest_run.current_stage))}`
                  : 'Start a run to populate workflow telemetry.'}
              </p>
              {overview?.latest_run ? <p className="muted">{formatDateTime(overview.latest_run.started_at)}</p> : null}
            </div>
            <div className="detail-card">
              <p className="eyebrow">Pipeline progress</p>
              {overview ? (
                <>
                  <div className="progress-meter">
                    <div
                      className="progress-meter-fill"
                      style={{
                        width: `${Math.max(
                          overview.progress.total
                            ? (overview.progress.done / Math.max(overview.progress.total, 1)) * 100
                            : (Object.values(overview.progress.stages).filter((stage) => stage.status === 'done').length /
                                Math.max(Object.keys(overview.progress.stages).length, 1)) *
                                100,
                          8,
                        )}%`,
                      }}
                    />
                  </div>
                  <p className="muted progress-meta">
                    {overview.progress.total
                      ? `${overview.progress.done}/${overview.progress.total} candidates processed`
                      : `${Object.values(overview.progress.stages).filter((stage) => stage.status === 'done').length}/${Object.keys(
                          overview.progress.stages,
                        ).length} stages complete`}
                  </p>
                </>
              ) : (
                <EmptyState message="Workflow progress will appear after the first tracked run." />
              )}
            </div>
          </div>

          <div className="agent-lane-grid">
            {agentLanes.map((lane) => (
              <article key={lane.name} className="detail-card">
                <p className="eyebrow">{lane.name}</p>
                <div className="lane-head">
                  <strong>{lane.detail}</strong>
                  <StatusPill value={lane.status} />
                </div>
              </article>
            ))}
          </div>

          {overview ? (
            <div className="stage-grid compact-grid">
              {Object.entries(overview.progress.stages).map(([name, stage]) => (
                <div key={name} className={`stage-card stage-${stage.status}`}>
                  <div className="stage-dot" />
                  <div>
                    <strong>{name}</strong>
                    <p>{stage.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : null}

          <div className="tracker-columns">
            <div className="log-panel">
              <p className="eyebrow">Recent workflow events</p>
              {latestEvents.length ? (
                latestEvents.slice(0, 8).map((event) => (
                  <div key={event.id} className="feed-item">
                    <span>{event.created_at.slice(11, 19)}</span>
                    <strong>{formatLabel(event.event_type)}</strong>
                    <p>{event.message}</p>
                  </div>
                ))
              ) : (
                <EmptyState message="No recent workflow events yet." />
              )}
            </div>
            <div className="log-panel">
              <p className="eyebrow">Recent runs</p>
              {recentRuns.length ? (
                <div className="run-stack">
                  {recentRuns.map((run) => (
                    <div key={run.run_id} className="detail-card">
                      <div className="lane-head">
                        <strong>{run.run_id}</strong>
                        <StatusPill value={run.status} />
                      </div>
                      <p className="muted">
                        {formatLabel(run.workflow_type)} · {formatLabel(run.current_stage)}
                      </p>
                      <p className="muted">
                        {formatDateTime(run.started_at)}
                        {run.finished_at ? ` · ${formatDateTime(run.finished_at)}` : ''}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState message="No tracked workflow runs yet." />
              )}
            </div>
          </div>
        </div>
      </Panel>

      <Panel title="Agent Studio" subtitle="Talk to DeerFlow, then simulate from the same workspace">
        <div className="settings-grid">
          <label>
            Strategy
            <select value={strategyType} onChange={(event) => setStrategyType(event.target.value)}>
              {(options?.strategy_options ?? ['momentum', 'mean_reversion', 'volume']).map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
          <label>
            Objective
            <select value={objective} onChange={(event) => setObjective(event.target.value)}>
              <option value="Fitness-first">Fitness-first</option>
              <option value="Sharpe-first">Sharpe-first</option>
              <option value="Balanced">Balanced</option>
              <option value="Exploration">Exploration</option>
            </select>
          </label>
          <label>
            Count
            <input type="number" value={count} onChange={(event) => setCount(Number(event.target.value))} />
          </label>
        </div>

        <label>
          Focus query
          <textarea rows={3} value={focusQuery} onChange={(event) => setFocusQuery(event.target.value)} />
        </label>
        <div className="panel-actions">
          <button className="ghost-button" onClick={() => void loadContext()} disabled={busy !== ''}>
            {busy === 'context' ? 'Refreshing…' : 'Refresh context'}
          </button>
        </div>

        {contextBundle ? (
          <div className="detail-card">
            <p className="eyebrow">Context bundle</p>
            <pre className="code-block">{contextBundle.context}</pre>
          </div>
        ) : null}

        <label>
          Agent prompt
          <textarea rows={5} value={prompt} onChange={(event) => setPrompt(event.target.value)} />
        </label>
        <div className="panel-actions">
          <button className="ghost-button" onClick={() => void runQuery()} disabled={busy !== ''}>
            {busy === 'query' ? 'Querying…' : 'Ask agents'}
          </button>
          <button className="ghost-button" onClick={() => void runGenerate()} disabled={busy !== ''}>
            {busy === 'generate' ? 'Generating…' : 'Generate alpha pack'}
          </button>
        </div>

        {responses ? (
          <div className="response-grid">
            {Object.entries((responses.responses ?? {}) as Record<string, string>).map(([agent, text]) => (
              <article key={agent} className="detail-card">
                <p className="eyebrow">{agent}</p>
                <pre className="code-block">{text}</pre>
              </article>
            ))}
          </div>
        ) : null}
      </Panel>

      <Panel title="Chatspace" subtitle="User and agent interaction history in one place">
        <div className="chatspace-shell">
          <div className="chatspace-feed">
            {chatMessages.length ? (
              chatMessages.map((item) => (
                <article key={item.id} className={`chat-bubble ${item.role}`}>
                  <div className="chat-bubble-head">
                    <strong>{item.role === 'user' ? 'User' : item.agent}</strong>
                    <span>{item.createdAt.slice(11, 19)}</span>
                  </div>
                  <MarkdownRenderer text={item.content} />
                </article>
              ))
            ) : (
              <EmptyState message="No chat yet. Send the first prompt to start the agent conversation." />
            )}
            {busy === 'chat' && (
              <article className="chat-bubble agent">
                <div className="chat-bubble-head">
                  <strong>DeerFlow</strong>
                  <span>Thinking...</span>
                </div>
                <div className="gemini-typing" style={{ marginTop: '0.5rem' }}>
                  <span />
                  <span />
                  <span />
                </div>
              </article>
            )}
          </div>

          <div className="chatspace-compose">
            <label>
              Message to agents
              <textarea
                rows={5}
                value={chatInput}
                onChange={(event) => setChatInput(event.target.value)}
                placeholder="Ask DeerFlow to critique or improve the current direction."
              />
            </label>
            <div className="panel-actions">
              <button className="ghost-button" onClick={() => void sendChat()} disabled={busy !== ''}>
                {busy === 'chat' ? 'Sendingâ€¦' : 'Send to chatspace'}
              </button>
            </div>
          </div>
        </div>
      </Panel>

      <Panel title="Candidate Lab" subtitle="Collect expressions, add your own, and run simulation">
        <label>
          Manual expression
          <input value={manualExpression} onChange={(event) => setManualExpression(event.target.value)} placeholder="rank(ts_mean(returns, 20))" />
        </label>
        <div className="panel-actions">
          <button
            className="ghost-button"
            onClick={() => {
              if (!manualExpression.trim()) return
              mergeCandidates({
                Manual: [{ expression: manualExpression.trim(), valid: true, errors: [], source: 'Manual' }],
              })
              setSelectedExpression(manualExpression.trim())
              setManualExpression('')
            }}
          >
            Add candidate
          </button>
        </div>

        {candidatePool.length ? (
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th />
                  <th>Expression</th>
                  <th>Source</th>
                  <th>Valid</th>
                  <th>Errors</th>
                </tr>
              </thead>
              <tbody>
                {candidatePool.map((item) => (
                  <tr key={`${item.source}-${item.expression}`}>
                    <td>
                      <input type="radio" checked={selectedExpression === item.expression} onChange={() => setSelectedExpression(item.expression)} />
                    </td>
                    <td>{item.expression}</td>
                    <td>{item.source}</td>
                    <td>{item.valid ? 'Yes' : 'No'}</td>
                    <td>{item.errors.join('; ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState message="No candidates yet. Ask an agent or add one manually." />
        )}

        <div className="panel-actions">
          <button className="ghost-button" onClick={() => void runSimulate()} disabled={busy !== ''}>
            {busy === 'simulate' ? 'Simulating…' : 'Simulate selected'}
          </button>
        </div>

        {simulation ? (
          <div className="detail-card">
            <p className="eyebrow">Simulation result</p>
            <div className="metrics-grid">
              <MetricCard label="Sharpe" value={formatNumber((simulation.metrics as Record<string, unknown>)?.sharpe)} detail={String(simulation.status ?? 'tested')} />
              <MetricCard label="Fitness" value={formatNumber((simulation.metrics as Record<string, unknown>)?.fitness)} detail="Post-simulation score" />
              <MetricCard label="Turnover" value={formatPercent((simulation.metrics as Record<string, unknown>)?.turnover)} detail="Observed turnover" />
              <MetricCard label="Drawdown" value={formatPercent((simulation.metrics as Record<string, unknown>)?.drawdown)} detail="Observed drawdown" />
            </div>
            <div className="review-list">
              {[...(simulation.pre_reviews as Array<Record<string, unknown>> ?? []), ...(simulation.post_reviews as Array<Record<string, unknown>> ?? [])].map((review, index) => (
                <div key={`sim-review-${index}`} className="review-card">
                  <strong>{String(review.agent)} · {String(review.stage)} · {String(review.verdict)}</strong>
                  <p>{String(review.summary)}</p>
                </div>
              ))}
            </div>
            {Number(simulation.alpha_run_id ?? 0) ? (
              <div className="panel-actions">
                <button className="ghost-button" onClick={() => onInspectAlpha(Number(simulation.alpha_run_id))}>
                  Open alpha detail
                </button>
              </div>
            ) : null}
          </div>
        ) : null}
      </Panel>
    </div>
  )
}

function SimulatingPage(props: {
  overviewState: LoadState<OverviewResponse> & { refetch: () => Promise<void> }
  onStop: () => Promise<void>
}) {
  const alphasState = usePolling(() => api.getAlphas({ limit: 50 }), [], 5000)

  if (props.overviewState.loading && !props.overviewState.data) return <LoadingState message="Loading simulation status…" />
  const data = props.overviewState.data
  const workflowDetail = data?.workflow_detail
  const queue = workflowDetail?.simulation_queue
  const active = queue?.active

  return (
    <div style={{ padding: '0 4px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <div>
          <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-text-primary)' }}>Simulating Now</h2>
          <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>Real-time cluster simulation pipeline and FIFO queue status</p>
        </div>
        <button
          className="btn-layout btn-sm-layout"
          disabled={!active}
          onClick={() => void props.onStop()}
        >
          Stop Current Sim
        </button>
      </div>

      {/* Active simulation section */}
      <Panel title="Current Candidate Simulation" subtitle={active ? 'Simulating candidate expression on backtesting engine' : 'No active simulation'}>
        {active ? (
          <div style={{ padding: '8px 0' }}>
            <div style={{ fontSize: '13px', color: 'var(--color-text-primary)', fontFamily: 'monospace', background: 'var(--color-background-tertiary)', padding: '10px', borderRadius: '6px', marginBottom: '10px', border: '0.5px solid var(--color-border-tertiary)' }}>
              {active.expression}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--color-text-secondary)', marginBottom: '6px' }}>
              <span>Engine Status</span>
              <span>Running ({formatDurationSeconds(active.waiting_seconds)} active)</span>
            </div>
            <div className="skill-bar-wrap-layout">
              <div className="skill-bar-layout" style={{ width: '100%', background: 'var(--color-text-info)', animation: 'pulse 2s infinite' }} />
            </div>
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <button
                className="btn-layout btn-sm-layout"
                style={{ background: 'var(--color-background-tertiary)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border-primary)' }}
                onClick={async () => {
                  try {
                    await api.unlockSimulationQueue();
                    alert('Queue unlocked! The next candidate will begin simulation shortly.');
                    void props.overviewState.refetch();
                  } catch (e: any) {
                    alert('Failed to unlock queue: ' + e.message);
                  }
                }}
              >
                Unlock Queue (Force Resume)
              </button>
              <button
                className="btn-layout btn-sm-layout"
                style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'rgb(239, 68, 68)', border: '1px solid rgba(239, 68, 68, 0.2)' }}
                onClick={async () => {
                  if (confirm('Are you sure you want to completely reset and clear the simulation queue?')) {
                    try {
                      await api.clearSimulationQueue();
                      alert('Queue fully cleared!');
                      void props.overviewState.refetch();
                    } catch (e: any) {
                      alert('Failed to clear queue: ' + e.message);
                    }
                  }
                }}
              >
                Clear Queue
              </button>
            </div>
          </div>
        ) : (
          <div>
            <EmptyState message="Simulation engine is currently idle." />
            <div style={{ display: 'flex', gap: '8px', marginTop: '12px', justifyContent: 'center' }}>
              <button
                className="btn-layout btn-sm-layout"
                style={{ background: 'var(--color-background-tertiary)', color: 'var(--color-text-primary)', border: '1px solid var(--color-border-primary)' }}
                onClick={async () => {
                  try {
                    await api.unlockSimulationQueue();
                    alert('Queue unlocked!');
                    void props.overviewState.refetch();
                  } catch (e: any) {
                    alert('Failed to unlock queue: ' + e.message);
                  }
                }}
              >
                Unlock Queue
              </button>
              <button
                className="btn-layout btn-sm-layout"
                style={{ background: 'rgba(239, 68, 68, 0.1)', color: 'rgb(239, 68, 68)', border: '1px solid rgba(239, 68, 68, 0.2)' }}
                onClick={async () => {
                  if (confirm('Are you sure you want to completely reset and clear the simulation queue?')) {
                    try {
                      await api.clearSimulationQueue();
                      alert('Queue fully cleared!');
                      void props.overviewState.refetch();
                    } catch (e: any) {
                      alert('Failed to clear queue: ' + e.message);
                    }
                  }
                }}
              >
                Clear Queue
              </button>
            </div>
          </div>
        )}
      </Panel>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '12px', marginTop: '12px' }}>
        {/* Waiting FIFO queue */}
        <Panel title="Waiting in Queue" subtitle={`${queue?.waiting?.length ?? 0} candidates waiting`}>
          {queue?.waiting?.length ? (
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {queue.waiting.map((item, idx) => (
                <div key={`${item.expression}-${idx}`} style={{ padding: '8px 10px', borderRadius: '4px', background: 'var(--color-background-primary)', border: '0.5px solid var(--color-border-tertiary)', marginBottom: '6px', fontSize: '11px', fontFamily: 'monospace', color: 'var(--color-text-secondary)', wordBreak: 'break-all' }}>
                  <span style={{ color: 'var(--color-text-tertiary)', marginRight: '6px' }}>#{idx + 1}</span>
                  {item.expression}
                </div>
              ))}
            </div>
          ) : (
            <EmptyState message="FIFO queue is empty." />
          )}
        </Panel>

        {/* Completed today */}
        <Panel title="Completed Today" subtitle="Recently completed simulation runs">
          {alphasState.loading && !alphasState.data ? (
            <LoadingState message="Loading completed simulations..." />
          ) : alphasState.data?.items?.length ? (
            <div style={{ overflowX: 'auto' }}>
              <table className="tbl-layout">
                <thead>
                  <tr>
                    <th>Candidate Expression</th>
                    <th>Sharpe</th>
                    <th>Fitness</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {alphasState.data.items.slice(0, 15).map((alpha: any) => {
                    const statusStr = String(alpha.status || 'unknown');
                    const isPassing = statusStr.toLowerCase() === 'passing' || alpha.sharpe >= 2.0;
                    const isFailed = statusStr.toLowerCase() === 'failed' || alpha.sharpe < 1.0;
                    const badgeClass = isPassing ? 'b-green' : isFailed ? 'b-red' : 'b-amber';
                    const statusText = isPassing ? 'Passing' : isFailed ? 'Failed' : 'Weak';

                    return (
                      <tr key={alpha.id}>
                        <td style={{ fontFamily: 'monospace', fontSize: '11px', maxWidth: '350px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={alpha.expression}>
                          <Link to={`/alphas/${alpha.id}`} style={{ color: 'inherit', textDecoration: 'none' }}>
                            {alpha.expression}
                          </Link>
                        </td>
                        <td>{formatNumber(alpha.sharpe, 2)}</td>
                        <td>{formatNumber(alpha.fitness, 2)}</td>
                        <td>
                          <span className={`badge ${badgeClass}`}>{statusText}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState message="No simulations completed today yet." />
          )}
        </Panel>
      </div>
    </div>
  )
}

function AgentSkillsPage() {
  const theoriesState = usePolling(() => api.getTheories({ limit: 20 }), [], 15000)

  const learningNotes = [
    {
      type: 'success',
      text: 'Market summary: low-momentum regime confirmed via ADX < 20. Favour mean-reversion family this week.',
    },
    {
      type: 'success',
      text: 'Paper: "Short-term reversal in equities" confirms 5-day lookback optimal. Quality score 0.89.',
    },
    {
      type: 'warning',
      text: 'Tech sector showing momentum divergence — avoid pure mean-rev in tech names. Monitor.',
    },
    {
      type: 'success',
      text: 'Recovery note: after gate fail on vol sig, increase decay parameter from 0.05 to 0.08.',
    },
    {
      type: 'info',
      text: 'Analysis: Mean-reversion signals show higher efficacy when volatility is above 20-day median.',
    }
  ]

  return (
    <div style={{ padding: '0 4px' }}>
      <div style={{ marginBottom: '12px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--color-text-primary)' }}>Agent Skills</h2>
        <p style={{ fontSize: '12px', color: 'var(--color-text-tertiary)' }}>Skill proficiencies and operational insights learned by DeerFlow</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
        {/* DeerFlow Notes */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <span style={{ width: '28px', height: '28px', borderRadius: '50%', background: 'var(--color-background-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-warning)' }}>
              <i className="ti ti-brain"></i>
            </span>
            <div>
              <div className="sec" style={{ margin: 0, padding: 0, border: 'none' }}>DeerFlow — theory explorer & alpha builder</div>
              <span style={{ fontSize: '11px', color: 'var(--color-text-tertiary)' }}>Mines academic literature, generates alphas, and evaluates performance</span>
            </div>
          </div>

          <div className="sec" style={{ fontSize: '11px', textTransform: 'uppercase', marginBottom: '6px' }}>DeerFlow — learning notes & insights</div>
          <div>
            {learningNotes.map((note, idx) => (
              <div key={idx} className="insight-row-layout">
                <span className="insight-icon-layout">
                  <i className={note.type === 'warning' ? 'ti ti-alert-triangle' : 'ti ti-check'} style={{ color: note.type === 'warning' ? 'var(--color-text-warning)' : 'var(--color-text-success)' }}></i>
                </span>
                <span style={{ color: 'var(--color-text-secondary)', fontSize: '11.5px', lineHeight: '1.4' }}>{note.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Theories mapped to skills */}
      <div style={{ marginTop: '12px' }}>
        <Panel title="Active Knowledge Base" subtitle="Strategy theories currently mapped to DeerFlow exploration pipeline">
          {theoriesState.loading && !theoriesState.data ? (
            <LoadingState message="Loading knowledge base theories..." />
          ) : theoriesState.data?.items?.length ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', padding: '6px 0' }}>
              {theoriesState.data.items.map((theory) => (
                <span key={theory.id} className="theory-tag-layout" title={theory.core_principle}>
                  {theory.title}
                </span>
              ))}
            </div>
          ) : (
            <EmptyState message="No theories registered in active knowledge base." />
          )}
        </Panel>
      </div>
    </div>
  )
}

export default App
