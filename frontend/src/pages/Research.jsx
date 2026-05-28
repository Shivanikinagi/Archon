import { useState, useEffect, useRef } from 'react'
import { useStore } from '../stores/useStore.js'
import { startResearch, getResearchStatus, getResearchReport } from '../services/api.js'
import {
  Search,
  Send,
  Loader2,
  CheckCircle,
  XCircle,
  Globe,
  BookOpen,
  Newspaper,
  FileText,
  Download,
  BrainCircuit,
  Database,
  Microscope,
  Network,
  ShieldCheck,
  Quote,
  FileCheck,
  Sparkles,
  ChevronRight,
  ExternalLink,
  GitBranch,
  Lightbulb,
  TrendingUp,
  BarChart3,
  Shield,
} from 'lucide-react'

const sourceOptions = [
  { id: 'web', label: 'Web', icon: Globe },
  { id: 'academic', label: 'Academic', icon: BookOpen },
  { id: 'news', label: 'News', icon: Newspaper },
]

const depthOptions = [
  { value: 'shallow', label: 'Quick', description: 'Fast overview (~5 sec)' },
  { value: 'moderate', label: 'Standard', description: 'Balanced depth (~15 sec)' },
  { value: 'deep', label: 'Deep', description: 'Comprehensive (~15 sec)' },
]

const SUGGESTED_QUERIES = [
  {
    query: 'How are Microsoft, OpenAI, NVIDIA, and Anthropic connected in the generative AI ecosystem?',
    icon: GitBranch,
    label: 'Relationship Analysis',
  },
  {
    query: 'Compare GPT-4o, Gemini 1.5, Claude 3.5, and Llama 3 on multimodal capabilities and benchmarks',
    icon: BarChart3,
    label: 'Model Comparison',
  },
  {
    query: 'Recent advancements in multimodal AI models: architectures, limitations, and research trends in 2024-2025',
    icon: TrendingUp,
    label: 'Research Trends',
  },
  {
    query: 'What are the key technical differences between transformer-based and diffusion-based generative models?',
    icon: Lightbulb,
    label: 'Technical Deep-Dive',
  },
  {
    query: 'How does AI agent infrastructure connect LLMs, tool use, memory systems, and planning frameworks?',
    icon: BrainCircuit,
    label: 'System Architecture',
  },
  {
    query: 'Compare RAG vs GraphRAG architectures: strengths, weaknesses, and when to use each',
    icon: BarChart3,
    label: 'Architecture Comparison',
  },
  {
    query: 'Evolution of transformer architectures after GPT-3: what changed and why it matters',
    icon: TrendingUp,
    label: 'Architecture Evolution',
  },
  {
    query: 'Top approaches for reducing hallucinations in LLMs: techniques, benchmarks, and trade-offs',
    icon: ShieldCheck,
    label: 'LLM Safety',
  },
  {
    query: 'Latest techniques in agentic AI systems: planning, tool use, and multi-agent coordination',
    icon: BrainCircuit,
    label: 'Agentic AI',
  },
  {
    query: 'Which companies invested in organizations developing generative AI models?',
    icon: GitBranch,
    label: 'Investment Network',
  },
  {
    query: 'Find relationships between AI chip companies and LLM providers',
    icon: Network,
    label: 'Supply Chain',
  },
  {
    query: 'Impact of recent EU AI regulations on generative AI companies',
    icon: Globe,
    label: 'Policy & AI',
  },
  {
    query: 'Recent breakthroughs in open-source LLMs: benchmarks, licensing, and community impact',
    icon: TrendingUp,
    label: 'Open Source',
  },
]

// Workflow pipeline steps with icons
const WORKFLOW_STEPS = [
  { key: 'planning', label: 'Planning Research', icon: BrainCircuit },
  { key: 'searching', label: 'Searching Sources', icon: Search },
  { key: 'extracting', label: 'Extracting Entities', icon: Microscope },
  { key: 'graph', label: 'Building Knowledge Graph', icon: Network },
  { key: 'analyzing', label: 'Analyzing Sources', icon: Database },
  { key: 'synthesizing', label: 'Synthesizing Report', icon: Sparkles },
  { key: 'factcheck', label: 'Fact Checking', icon: ShieldCheck },
  { key: 'citations', label: 'Generating Citations', icon: Quote },
  { key: 'finalizing', label: 'Finalizing Report', icon: FileCheck },
]

function ConfidencePanel({ scores }) {
  if (!scores) return null

  const sectionMap = {
    executive_summary: 'Executive Summary',
    recent_advancements: 'Recent Advancements',
    technical_architecture: 'Technical Architecture',
    competitive_landscape: 'Competitive Landscape',
    research_trends: 'Research Trends',
    limitations: 'Limitations',
    future_outlook: 'Future Outlook',
  }

  const getColor = (score) => {
    if (score >= 0.85) return 'bg-green-500'
    if (score >= 0.7) return 'bg-blue-500'
    if (score >= 0.55) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getTextColor = (score) => {
    if (score >= 0.85) return 'text-green-700 dark:text-green-400'
    if (score >= 0.7) return 'text-blue-700 dark:text-blue-400'
    if (score >= 0.55) return 'text-yellow-700 dark:text-yellow-400'
    return 'text-red-700 dark:text-red-400'
  }

  return (
    <div className="card mt-4">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2 text-sm">
          <Shield className="w-4 h-4 text-primary-600" />
          Confidence Assessment
        </h4>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${getColor(scores.overall || 0).replace('bg-', 'bg-').replace('500', '100')} dark:bg-opacity-20 ${getTextColor(scores.overall || 0)}`}>
          Overall: {((scores.overall || 0) * 100).toFixed(0)}%
        </span>
      </div>
      <div className="space-y-2">
        {Object.entries(sectionMap).map(([key, label]) => {
          const score = scores[key] || 0
          return (
            <div key={key} className="flex items-center gap-3">
              <span className="text-xs text-gray-600 dark:text-gray-400 w-32 truncate">{label}</span>
              <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-1000 ${getColor(score)}`}
                  style={{ width: `${score * 100}%` }}
                />
              </div>
              <span className={`text-xs font-bold w-10 text-right ${getTextColor(score)}`}>
                {(score * 100).toFixed(0)}%
              </span>
            </div>
          )
        })}
      </div>
      {scores.rationale && (
        <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-2 italic">
          {scores.rationale}
        </p>
      )}
    </div>
  )
}

function WorkflowPipeline({ currentStep, progress }) {
  // Map step strings to indices
  const stepIndex = WORKFLOW_STEPS.findIndex((s) =>
    currentStep?.toLowerCase().includes(s.key) ||
    (s.key === 'synthesizing' && currentStep?.toLowerCase().includes('synthes')) ||
    (s.key === 'synthesizing' && currentStep?.toLowerCase().includes('ai is')) ||
    (s.key === 'planning' && currentStep?.toLowerCase().includes('initial')) ||
    (s.key === 'planning' && currentStep?.toLowerCase().includes('planning')) ||
    (s.key === 'searching' && currentStep?.toLowerCase().includes('search')) ||
    (s.key === 'extracting' && currentStep?.toLowerCase().includes('extract')) ||
    (s.key === 'graph' && currentStep?.toLowerCase().includes('graph')) ||
    (s.key === 'analyzing' && currentStep?.toLowerCase().includes('analyz')) ||
    (s.key === 'analyzing' && currentStep?.toLowerCase().includes('ranking')) ||
    (s.key === 'factcheck' && currentStep?.toLowerCase().includes('fact')) ||
    (s.key === 'citations' && currentStep?.toLowerCase().includes('citation')) ||
    (s.key === 'finalizing' && currentStep?.toLowerCase().includes('final')) ||
    (s.key === 'finalizing' && currentStep?.toLowerCase().includes('reasoning')) ||
    (s.key === 'finalizing' && currentStep?.toLowerCase().includes('complete'))
  )

  const activeIndex = stepIndex >= 0 ? stepIndex : Math.floor(progress * WORKFLOW_STEPS.length)

  return (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
        Research Pipeline
      </h4>
      <div className="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-9 gap-2">
        {WORKFLOW_STEPS.map((step, idx) => {
          const Icon = step.icon
          const isDone = idx < activeIndex
          const isActive = idx === activeIndex
          const isPending = idx > activeIndex

          return (
            <div
              key={step.key}
              className={`flex flex-col items-center text-center p-2 rounded-lg transition-all duration-500 ${
                isDone
                  ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800'
                  : isActive
                    ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-300 dark:border-primary-700 ring-2 ring-primary-200 dark:ring-primary-800 animate-pulse'
                    : 'bg-gray-50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 opacity-50'
              }`}
            >
              <div
                className={`p-1.5 rounded-full mb-1 ${
                  isDone
                    ? 'bg-green-100 dark:bg-green-800 text-green-600 dark:text-green-400'
                    : isActive
                      ? 'bg-primary-100 dark:bg-primary-800 text-primary-600 dark:text-primary-400'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-400 dark:text-gray-500'
                }`}
              >
                {isDone ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <span
                className={`text-[10px] font-medium leading-tight ${
                  isDone
                    ? 'text-green-700 dark:text-green-400'
                    : isActive
                      ? 'text-primary-700 dark:text-primary-400'
                      : 'text-gray-500 dark:text-gray-500'
                }`}
              >
                {step.label}
              </span>
              {isActive && (
                <Loader2 className="w-3 h-3 mt-1 animate-spin text-primary-500" />
              )}
            </div>
          )
        })}
      </div>
      <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
        <GitBranch className="w-3 h-3" />
        <span>Current: {currentStep || 'Processing...'}</span>
      </div>
    </div>
  )
}

function ReportContent({ content, sources }) {
  // Simple markdown-like rendering with citation linkification
  const lines = content.split('\n')
  const rendered = []
  let inCode = false
  let inTable = false

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // Code blocks
    if (line.trim().startsWith('```')) {
      inCode = !inCode
      rendered.push(
        <pre
          key={i}
          className="bg-gray-900 text-gray-100 p-3 rounded-lg text-xs overflow-x-auto my-2 font-mono"
        >
          {line.replace(/```/g, '')}
        </pre>
      )
      continue
    }
    if (inCode) {
      rendered.push(
        <pre
          key={i}
          className="bg-gray-900 text-gray-100 px-3 text-xs overflow-x-auto font-mono"
        >
          {line}
        </pre>
      )
      continue
    }

    // Tables
    if (line.trim().startsWith('|')) {
      if (!inTable) {
        inTable = true
        rendered.push(
          <div key={i} className="overflow-x-auto my-3">
            <table className="min-w-full text-xs border-collapse">
              <tbody>
                <tr className="bg-gray-100 dark:bg-gray-800">
                  {line
                    .split('|')
                    .filter((c) => c.trim())
                    .map((cell, ci) => (
                      <th
                        key={ci}
                        className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-left font-semibold text-gray-700 dark:text-gray-300"
                      >
                        {cell.trim()}
                      </th>
                    ))}
                </tr>
              </tbody>
            </table>
          </div>
        )
      } else if (!line.trim().match(/^\|[\s\-]+\|/)) {
        // Data row
        const prev = rendered[rendered.length - 1]
        if (prev && prev.props.children?.props?.children?.props?.children) {
          // Append to existing table - this is a simplified approach
          rendered.push(
            <div key={i} className="overflow-x-auto">
              <table className="min-w-full text-xs border-collapse">
                <tbody>
                  <tr className="bg-white dark:bg-gray-900">
                    {line
                      .split('|')
                      .filter((c) => c.trim())
                      .map((cell, ci) => (
                        <td
                          key={ci}
                          className="border border-gray-300 dark:border-gray-600 px-2 py-1 text-gray-700 dark:text-gray-300"
                        >
                          {cell.trim()}
                        </td>
                      ))}
                  </tr>
                </tbody>
              </table>
            </div>
          )
        }
      }
      continue
    } else {
      inTable = false
    }

    // Headers
    if (line.startsWith('# ')) {
      rendered.push(
        <h1 key={i} className="text-xl font-bold text-gray-900 dark:text-white mt-6 mb-3">
          {line.replace('# ', '')}
        </h1>
      )
      continue
    }
    if (line.startsWith('## ')) {
      rendered.push(
        <h2 key={i} className="text-lg font-bold text-gray-900 dark:text-white mt-5 mb-2">
          {line.replace('## ', '')}
        </h2>
      )
      continue
    }
    if (line.startsWith('### ')) {
      rendered.push(
        <h3 key={i} className="text-base font-semibold text-gray-800 dark:text-gray-200 mt-4 mb-2">
          {line.replace('### ', '')}
        </h3>
      )
      continue
    }

    // Bold
    let processed = line
    processed = processed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    processed = processed.replace(/\*(.*?)\*/g, '<em>$1</em>')

    // Citations [1], [2] etc. → links
    if (sources && sources.length > 0) {
      processed = processed.replace(/\[(\d+)\]/g, (match, num) => {
        const src = sources.find((s) => s.index === parseInt(num) || s.index === num)
        if (src && src.url) {
          return `<a href="${src.url}" target="_blank" rel="noopener" class="inline-flex items-center gap-0.5 px-1 py-0.5 rounded bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-[10px] font-bold hover:underline">[${num}]<svg class="w-2 h-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/></svg></a>`
        }
        return match
      })
    }

    // Empty line
    if (!line.trim()) {
      rendered.push(<div key={i} className="h-2" />)
      continue
    }

    // Horizontal rule
    if (line.trim() === '---') {
      rendered.push(<hr key={i} className="my-4 border-gray-200 dark:border-gray-700" />)
      continue
    }

    // List items
    if (line.trim().startsWith('- ')) {
      rendered.push(
        <li key={i} className="ml-4 text-sm text-gray-700 dark:text-gray-300 leading-relaxed list-disc">
          <span dangerouslySetInnerHTML={{ __html: line.replace('- ', '') }} />
        </li>
      )
      continue
    }

    // Numbered list
    const numMatch = line.match(/^(\d+)\.\s+(.*)/)
    if (numMatch) {
      rendered.push(
        <div key={i} className="ml-4 text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
          <span className="font-semibold text-primary-600 dark:text-primary-400">{numMatch[1]}.</span>{' '}
          <span dangerouslySetInnerHTML={{ __html: numMatch[2] }} />
        </div>
      )
      continue
    }

    // Default paragraph
    rendered.push(
      <p
        key={i}
        className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed"
        dangerouslySetInnerHTML={{ __html: processed }}
      />
    )
  }

  return <div className="space-y-1">{rendered}</div>
}

function SourcesPanel({ sources }) {
  if (!sources || sources.length === 0) return null

  return (
    <div className="card mt-4">
      <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
        <Database className="w-4 h-4 text-primary-600" />
        Sources & References
      </h4>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {sources.map((src) => (
          <a
            key={src.index}
            href={src.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-start gap-2 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors group"
          >
            <span className="flex-shrink-0 inline-flex items-center justify-center w-5 h-5 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-[10px] font-bold">
              {src.index}
            </span>
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-900 dark:text-white truncate group-hover:text-primary-600 dark:group-hover:text-primary-400">
                {src.title}
              </p>
              <p className="text-[10px] text-gray-500 dark:text-gray-400 truncate">{src.url}</p>
              <span
                className={`inline-block mt-0.5 px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  src.source_type === 'academic'
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300'
                    : 'bg-green-50 text-green-700 dark:bg-green-900/20 dark:text-green-300'
                }`}
              >
                {src.source_type}
              </span>
            </div>
            <ExternalLink className="w-3 h-3 text-gray-400 flex-shrink-0 mt-1 opacity-0 group-hover:opacity-100 transition-opacity" />
          </a>
        ))}
      </div>
    </div>
  )
}

export default function Research() {
  const {
    currentResearch,
    researchProgress,
    researchStatus,
    setCurrentResearch,
    setResearchProgress,
    setResearchStatus,
    resetResearch,
  } = useStore()

  const [query, setQuery] = useState('')
  const [depth, setDepth] = useState('moderate')
  const [sources, setSources] = useState(['web'])
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')
  const [currentStep, setCurrentStep] = useState('')
  const intervalRef = useRef(null)

  const toggleSource = (sourceId) => {
    setSources((prev) =>
      prev.includes(sourceId)
        ? prev.filter((s) => s !== sourceId)
        : [...prev, sourceId]
    )
  }

  const handleStart = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    resetResearch()
    setReport(null)
    setError('')
    setResearchStatus('running')
    setResearchProgress(0)
    setCurrentStep('Initializing...')

    try {
      const response = await startResearch({
        query: query.trim(),
        depth,
        source_types: sources,
      })

      const sessionId = response.session_id
      setCurrentResearch({ sessionId, query: query.trim() })
      pollStatus(sessionId)
    } catch (err) {
      setResearchStatus('failed')
      let errorMessage = 'Failed to start research'
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail
        } else if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map((e) => `${e.loc.join('.')}: ${e.msg}`).join(', ')
        } else {
          errorMessage = JSON.stringify(err.response.data.detail)
        }
      } else if (err.message) {
        errorMessage = err.message
      }
      setError(errorMessage)
      setResearchProgress(0)
    }
  }

  const pollStatus = (sessionId) => {
    if (intervalRef.current) clearInterval(intervalRef.current)

    intervalRef.current = setInterval(async () => {
      try {
        const status = await getResearchStatus(sessionId)
        const progressPercent = Math.round((status.progress || 0) * 100)
        setResearchProgress(progressPercent)
        setCurrentStep(status.current_step || '')

        if (status.status === 'completed') {
          setResearchStatus('completed')
          setResearchProgress(100)
          clearInterval(intervalRef.current)
          fetchReport(sessionId)
        } else if (status.status === 'failed') {
          setResearchStatus('failed')
          setError(status.error || 'Research failed')
          clearInterval(intervalRef.current)
        }
      } catch (err) {
        console.error('Poll error:', err)
        if (err.response?.status === 404) {
          setResearchStatus('failed')
          setError('Research session not found. The server may have restarted. Please try again.')
          clearInterval(intervalRef.current)
        } else if (err.code === 'ECONNABORTED' || err.code === 'ERR_NETWORK' || !err.response) {
          setResearchStatus('failed')
          setError('Cannot connect to research server. Please make sure the backend is running.')
          clearInterval(intervalRef.current)
        }
      }
    }, 2000)
  }

  const fetchReport = async (sessionId) => {
    try {
      const reportData = await getResearchReport(sessionId)
      setReport(reportData)
    } catch (err) {
      setError('Failed to fetch report')
    }
  }

  const handleExport = () => {
    if (!report || !report.content) return
    const blob = new Blob([report.content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `research-report-${currentResearch?.query?.replace(/\s+/g, '-').toLowerCase() || 'export'}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [])

  const isRunning = researchStatus === 'running'

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Research</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          Enter a query to start your deep research
        </p>
      </div>

      {/* Query form */}
      <div className="card space-y-6">
        <form onSubmit={handleStart} className="space-y-4">
          <div>
            <label className="label">Research Query</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                className="input pl-10"
                placeholder="What do you want to research?"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={isRunning}
              />
            </div>
            {/* Suggested Queries */}
            <div className="mt-2 flex flex-wrap gap-2">
              {SUGGESTED_QUERIES.map((sq) => {
                const Icon = sq.icon
                return (
                  <button
                    key={sq.query}
                    type="button"
                    onClick={() => setQuery(sq.query)}
                    disabled={isRunning}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-gray-100 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-700 text-[11px] text-gray-600 dark:text-gray-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 hover:border-primary-300 dark:hover:border-primary-700 hover:text-primary-700 dark:hover:text-primary-300 transition-colors"
                    title={sq.query}
                  >
                    <Icon className="w-3 h-3" />
                    <span className="truncate max-w-[200px]">{sq.label}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Depth selector */}
          <div>
            <label className="label">Research Depth</label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {depthOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setDepth(option.value)}
                  disabled={isRunning}
                  className={`p-3 rounded-lg border text-left transition-colors ${
                    depth === option.value
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  <p className="font-medium text-gray-900 dark:text-white">{option.label}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {option.description}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Source checkboxes */}
          <div>
            <label className="label">Sources</label>
            <div className="flex flex-wrap gap-3">
              {sourceOptions.map((source) => {
                const Icon = source.icon
                const isSelected = sources.includes(source.id)
                return (
                  <button
                    key={source.id}
                    type="button"
                    onClick={() => toggleSource(source.id)}
                    disabled={isRunning}
                    className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors ${
                      isSelected
                        ? 'border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-300'
                        : 'border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    {source.label}
                  </button>
                )
              })}
            </div>
          </div>

          <button
            type="submit"
            disabled={isRunning || !query.trim()}
            className="btn-primary w-full sm:w-auto disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Researching...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Start Research
              </>
            )}
          </button>
        </form>
      </div>

      {/* Progress + Workflow */}
      {isRunning && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between mb-1">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-primary-600 dark:text-primary-400" />
              Research in progress
            </h3>
            <span className="text-sm font-medium text-primary-600 dark:text-primary-400">
              {researchProgress}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-primary-500 to-primary-600 dark:from-primary-400 dark:to-primary-500 h-2 rounded-full transition-all duration-700"
              style={{ width: `${researchProgress}%` }}
            />
          </div>

          {/* Workflow Pipeline */}
          <WorkflowPipeline currentStep={currentStep} progress={researchProgress / 100} />

          <p className="text-xs text-gray-500 dark:text-gray-400">
            Query: <span className="font-medium">{currentResearch?.query}</span>
          </p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 flex items-start gap-3">
          <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Report */}
      {report && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
                  Research Report
                </h3>
                <span className="text-xs px-2 py-1 rounded-full bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 font-medium">
                  {report.word_count?.toLocaleString() || '?'} words
                </span>
                <span className="text-xs px-2 py-1 rounded-full bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400 font-medium">
                  {report.sources?.length || 0} sources
                </span>
                {report.confidence_scores?.overall !== undefined && (
                  <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                    report.confidence_scores.overall >= 0.85
                      ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                      : report.confidence_scores.overall >= 0.7
                        ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400'
                        : report.confidence_scores.overall >= 0.55
                          ? 'bg-yellow-50 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400'
                          : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
                  }`}>
                    {(report.confidence_scores.overall * 100).toFixed(0)}% confidence
                  </span>
                )}
              </div>
              <button onClick={handleExport} className="btn-secondary text-sm">
                <Download className="w-4 h-4 mr-2" />
                Export
              </button>
            </div>

            <div className="prose dark:prose-invert max-w-none">
              {report.content || report.report ? (
                <ReportContent content={report.content || report.report} sources={report.sources} />
              ) : (
                <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                  <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-auto">
                    {JSON.stringify(report, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>

          {/* Sources Panel */}
          <SourcesPanel sources={report.sources} />

          {/* Confidence Scores */}
          <ConfidencePanel scores={report.confidence_scores} />
        </div>
      )}
    </div>
  )
}
