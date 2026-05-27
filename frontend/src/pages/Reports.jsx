import { useEffect, useState } from 'react'
import { useStore } from '../stores/useStore.js'
import { listReports, getResearchReport } from '../services/api.js'
import {
  FileText,
  Search,
  Filter,
  X,
  Eye,
  Calendar,
  CheckCircle,
  Clock,
  Loader2,
  Download,
} from 'lucide-react'

export default function Reports() {
  const { reports, setReports } = useStore()
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [selectedReport, setSelectedReport] = useState(null)
  const [reportContent, setReportContent] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingReport, setIsLoadingReport] = useState(false)

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const data = await listReports()
        setReports(data.reports || data || [])
      } catch (err) {
        console.error('Failed to fetch reports:', err)
      } finally {
        setIsLoading(false)
      }
    }
    fetchReports()
  }, [setReports])

  const filteredReports = (reports || []).filter((report) => {
    const matchesSearch = (report.query || report.title || '')
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
    const matchesStatus =
      statusFilter === 'all' || report.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const openReport = async (report) => {
    setSelectedReport(report)
    setIsLoadingReport(true)
    setReportContent(null)

    try {
      if (report.session_id || report.id) {
        const content = await getResearchReport(report.session_id || report.id)
        setReportContent(content)
      }
    } catch (err) {
      console.error('Failed to fetch report content:', err)
    } finally {
      setIsLoadingReport(false)
    }
  }

  const closeReport = () => {
    setSelectedReport(null)
    setReportContent(null)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600 dark:text-primary-400" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Reports</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          Browse and search your generated research reports
        </p>
      </div>

      {/* Filters */}
      <div className="card flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            className="input pl-10"
            placeholder="Search reports..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500" />
          <select
            className="input py-2 w-40"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">All Status</option>
            <option value="completed">Completed</option>
            <option value="running">Running</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Reports list */}
      <div className="space-y-3">
        {filteredReports.length === 0 ? (
          <div className="card text-center py-12">
            <FileText className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" />
            <p className="text-gray-500 dark:text-gray-400">
              {searchTerm || statusFilter !== 'all'
                ? 'No reports match your filters'
                : 'No reports yet. Start a research to generate one.'}
            </p>
          </div>
        ) : (
          filteredReports.map((report) => (
            <div
              key={report.id || report.session_id}
              className="card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => openReport(report)}
            >
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-primary-50 dark:bg-primary-900/20 flex-shrink-0">
                  <FileText className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                </div>
                <div className="min-w-0">
                  <h3 className="font-medium text-gray-900 dark:text-white truncate">
                    {report.query || report.title || 'Untitled Report'}
                  </h3>
                  <div className="flex items-center gap-3 mt-1 text-sm text-gray-500 dark:text-gray-400">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(report.created_at || report.updated_at || Date.now()).toLocaleDateString()}
                    </span>
                    {report.depth && (
                      <span className="capitalize">{report.depth} depth</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${
                  report.status === 'completed'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                    : report.status === 'running'
                    ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
                    : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                }`}>
                  {report.status === 'completed' && <CheckCircle className="w-3 h-3" />}
                  {report.status === 'running' && <Clock className="w-3 h-3" />}
                  {report.status}
                </span>
                <button className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                  <Eye className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Report viewer modal */}
      {selectedReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
            {/* Modal header */}
            <div className="flex items-center justify-between p-4 lg:p-6 border-b border-gray-200 dark:border-gray-700">
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {selectedReport.query || selectedReport.title || 'Report'}
                </h2>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {new Date(selectedReport.created_at || Date.now()).toLocaleString()}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button className="btn-secondary text-sm">
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </button>
                <button
                  onClick={closeReport}
                  className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal content */}
            <div className="flex-1 overflow-y-auto p-4 lg:p-6">
              {isLoadingReport ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary-600 dark:text-primary-400" />
                </div>
              ) : reportContent ? (
                <div className="prose dark:prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                    {reportContent.content || reportContent.report || JSON.stringify(reportContent, null, 2)}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                  <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
                  <p>Report content not available</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
