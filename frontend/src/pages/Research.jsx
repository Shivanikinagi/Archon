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
} from 'lucide-react'

const sourceOptions = [
  { id: 'web', label: 'Web', icon: Globe },
  { id: 'academic', label: 'Academic', icon: BookOpen },
  { id: 'news', label: 'News', icon: Newspaper },
]

const depthOptions = [
  { value: 'shallow', label: 'Quick', description: 'Fast overview (~5 min)' },
  { value: 'moderate', label: 'Standard', description: 'Balanced depth (~15 min)' },
  { value: 'deep', label: 'Deep', description: 'Comprehensive (~30 min)' },
]

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
    setResearchProgress(10)

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
      // Handle different error formats
      let errorMessage = 'Failed to start research'
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail
        } else if (Array.isArray(err.response.data.detail)) {
          // Validation errors from FastAPI
          errorMessage = err.response.data.detail.map(e => `${e.loc.join('.')}: ${e.msg}`).join(', ')
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
        setResearchProgress(status.progress || 0)

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
      }
    }, 3000)
  }

  const fetchReport = async (sessionId) => {
    try {
      const reportData = await getResearchReport(sessionId)
      setReport(reportData)
    } catch (err) {
      setError('Failed to fetch report')
    }
  }

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [])

  const isRunning = researchStatus === 'running'

  return (
    <div className="max-w-4xl mx-auto space-y-6">
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

      {/* Progress */}
      {isRunning && (
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-primary-600 dark:text-primary-400" />
              Research in progress
            </h3>
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
              {researchProgress}%
            </span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
            <div
              className="bg-primary-600 dark:bg-primary-500 h-2.5 rounded-full transition-all duration-500"
              style={{ width: `${researchProgress}%` }}
            />
          </div>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Query: {currentResearch?.query}
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
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
              Research Report
            </h3>
            <button className="btn-secondary text-sm">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
          </div>
          <div className="prose dark:prose-invert max-w-none">
            {report.content || report.report ? (
              <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                {report.content || report.report}
              </div>
            ) : (
              <div className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-auto">
                  {JSON.stringify(report, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
