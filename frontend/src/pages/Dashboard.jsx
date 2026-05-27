import { useEffect, useState } from 'react'
import { useStore } from '../stores/useStore.js'
import { listReports, listDocuments } from '../services/api.js'
import {
  Search,
  FileText,
  Database,
  Activity,
  TrendingUp,
  Clock,
  Loader2,
} from 'lucide-react'

export default function Dashboard() {
  const { reports, documents, setReports, setDocuments } = useStore()
  const [stats, setStats] = useState({
    totalResearches: 0,
    totalDocuments: 0,
    completedResearches: 0,
    recentActivity: [],
  })
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [reportsData, documentsData] = await Promise.all([
          listReports(),
          listDocuments(),
        ])

        const reportsList = reportsData.reports || reportsData || []
        const documentsList = documentsData.documents || documentsData || []

        setReports(reportsList)
        setDocuments(documentsList)

        setStats({
          totalResearches: reportsList.length,
          totalDocuments: documentsList.length,
          completedResearches: reportsList.filter((r) => r.status === 'completed').length,
          recentActivity: [
            ...reportsList.slice(0, 5).map((r) => ({
              type: 'research',
              title: r.query || r.title || 'Research',
              date: r.created_at || r.updated_at || new Date().toISOString(),
              status: r.status,
            })),
          ],
        })
      } catch (err) {
        console.error('Dashboard fetch error:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [setReports, setDocuments])

  const statCards = [
    {
      label: 'Total Researches',
      value: stats.totalResearches,
      icon: Search,
      color: 'text-primary-600 dark:text-primary-400',
      bg: 'bg-primary-50 dark:bg-primary-900/20',
    },
    {
      label: 'Total Documents',
      value: stats.totalDocuments,
      icon: Database,
      color: 'text-emerald-600 dark:text-emerald-400',
      bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    },
    {
      label: 'Completed',
      value: stats.completedResearches,
      icon: TrendingUp,
      color: 'text-amber-600 dark:text-amber-400',
      bg: 'bg-amber-50 dark:bg-amber-900/20',
    },
    {
      label: 'Active Sessions',
      value: stats.totalResearches - stats.completedResearches,
      icon: Activity,
      color: 'text-rose-600 dark:text-rose-400',
      bg: 'bg-rose-50 dark:bg-rose-900/20',
    },
  ]

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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="mt-1 text-gray-600 dark:text-gray-400">
          Overview of your research activities
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.label} className="card flex items-center">
              <div className={`p-3 rounded-lg ${stat.bg}`}>
                <Icon className={`w-6 h-6 ${stat.color}`} />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  {stat.label}
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stat.value}
                </p>
              </div>
            </div>
          )
        })}
      </div>

      {/* Recent activity */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recent Activity
          </h2>
          <a href="/reports" className="text-sm text-primary-600 dark:text-primary-400 hover:underline">
            View all
          </a>
        </div>

        {stats.recentActivity.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No recent activity</p>
          </div>
        ) : (
          <div className="space-y-3">
            {stats.recentActivity.map((activity, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${
                    activity.type === 'research'
                      ? 'bg-primary-50 dark:bg-primary-900/20'
                      : 'bg-emerald-50 dark:bg-emerald-900/20'
                  }`}>
                    {activity.type === 'research' ? (
                      <Search className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                    ) : (
                      <FileText className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-xs sm:max-w-sm">
                      {activity.title}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(activity.date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                  activity.status === 'completed'
                    ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
                    : activity.status === 'running'
                    ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300'
                    : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                }`}>
                  {activity.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
